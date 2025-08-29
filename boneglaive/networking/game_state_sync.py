#!/usr/bin/env python3
"""
Game state synchronization for multiplayer games.
Handles serializing, transmitting, and applying game state updates.
"""

import copy
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from boneglaive.game.engine import Game
from boneglaive.networking.network_interface import MessageType, NetworkInterface
from boneglaive.networking.game_state_serializer import game_state_serializer
from boneglaive.utils.debug import debug_config, logger

class GameStateSync:
    """
    Handles game state synchronization between network players.
    """
    
    def __init__(self, game: Game, network: NetworkInterface, multiplayer_manager=None):
        self.game = game
        self.network = network
        self.multiplayer_manager = multiplayer_manager  # Reference to multiplayer manager for chat messages
        self.ui = None  # UI reference for animations
        self.last_sync_time = 0
        self.sync_interval = 0.5  # Seconds between state syncs
        self.last_sent_state = {}
        self.received_states = []
        self.pending_actions = []
        
        # Track completed turn states to prevent double-processing
        self.completed_turn_states = {}  # {player_num: turn_number}
        self.processed_turn_transitions = {}  # {(turn_number, player): True} - track which player/turn combos had transitions processed
        
        # Register message handlers
        # OLD GAME_STATE handler removed - Phase 5 uses GAME_STATE_BATCH only
        self.network.register_message_handler(
            MessageType.PLAYER_ACTION, self._handle_player_action
        )
        self.network.register_message_handler(
            MessageType.SETUP_ACTION, self._handle_setup_action
        )
        self.network.register_message_handler(
            MessageType.SETUP_PHASE_TRANSITION, self._handle_setup_phase_transition
        )
        self.network.register_message_handler(
            MessageType.SETUP_COMPLETE, self._handle_setup_complete
        )
        self.network.register_message_handler(
            MessageType.TURN_TRANSITION, self._handle_turn_transition
        )
        self.network.register_message_handler(
            MessageType.TURN_COMPLETE, self._handle_turn_complete
        )
        self.network.register_message_handler(
            MessageType.MESSAGE_LOG_BATCH, self._handle_message_log_batch
        )
        self.network.register_message_handler(
            MessageType.PARITY_CHECK, self._handle_parity_check
        )
        self.network.register_message_handler(
            MessageType.MESSAGE_LOG_SYNC_REQUEST, self._handle_sync_request
        )
        self.network.register_message_handler(
            MessageType.MESSAGE_LOG_FULL_SYNC, self._handle_full_sync
        )
        # Game state synchronization handlers
        self.network.register_message_handler(
            MessageType.GAME_STATE_BATCH, self._handle_game_state_batch
        )
        self.network.register_message_handler(
            MessageType.GAME_STATE_PARITY_CHECK, self._handle_game_state_parity_check
        )
        self.network.register_message_handler(
            MessageType.GAME_STATE_SYNC_REQUEST, self._handle_game_state_sync_request
        )
        self.network.register_message_handler(
            MessageType.GAME_STATE_FULL_SYNC, self._handle_game_state_full_sync
        )
    
    def set_ui_reference(self, ui) -> None:
        """Set the UI reference for animations."""
        self.ui = ui
    
    def can_act_in_setup(self) -> bool:
        """
        Check if the current player can take setup actions.
        Only the active setup player should be able to place units.
        """
        if not self.game.setup_phase:
            return True  # Not in setup phase, normal game rules apply
        
        # Get the network player number (1 for host, 2 for client)
        network_player = self.network.get_player_number()
        
        # Only allow actions if it's this player's setup turn
        return self.game.setup_player == network_player
    
    def update(self) -> None:
        """
        Update network state. Should be called every frame.
        """
        # Process any incoming messages
        self.network.receive_messages()
        
        # Apply any pending actions
        self._apply_pending_actions()
        
        # Sync game state if host and enough time has passed
        # OLD GAME STATE SYNC DISABLED - Phase 5 uses batch system only
        # The old continuous sync system conflicts with Phase 5 batch system
        # Game state sync now happens only at end-of-turn via GAME_STATE_BATCH messages
        pass
    
    def _sync_game_state(self) -> None:
        """
        Serialize and send the current game state.
        Only the host should do this.
        """
        if not self.network.is_host():
            return
        
        # Don't sync game state during setup phase - setup has its own message handling
        if self.game.setup_phase:
            return
        
        # Serialize game state
        state = self._serialize_game_state()
        
        # Only send if state has changed
        state_hash = hash(json.dumps(state, sort_keys=True))
        last_hash = hash(json.dumps(self.last_sent_state, sort_keys=True)) if self.last_sent_state else 0
        
        if state_hash != last_hash:
            # Send state to other player
            self.network.send_message(MessageType.GAME_STATE, {
                "state": state,
                "timestamp": time.time()
            })
            
            self.last_sent_state = state
    
    def _serialize_game_state(self) -> Dict[str, Any]:
        """
        OLD BASIC SERIALIZER - DISABLED for Phase 5
        This basic serializer conflicts with comprehensive Phase 5 game_state_serializer
        Phase 5 serializes 50+ properties vs this basic 10-property version
        """
        logger.warning("OLD_SERIALIZER: Called old _serialize_game_state - should use game_state_serializer.serialize_game_state() instead")
        return {"disabled": "old_system", "use": "game_state_serializer.serialize_game_state()"}
    
    def _deserialize_game_state(self, state: Dict[str, Any]) -> None:
        """
        OLD BASIC DESERIALIZER - DISABLED for Phase 5
        This basic deserializer conflicts with comprehensive Phase 5 system
        Phase 5 handles 50+ properties, status effects, skills, visual indicators, etc.
        """
        logger.warning("OLD_DESERIALIZER: Called old _deserialize_game_state - should use game_state_serializer.deserialize_game_state() instead")
        return  # Disabled - Phase 5 uses comprehensive deserializer
        # Update game state
        self.game.turn = state["turn"]
        self.game.current_player = state["current_player"]
        self.game.winner = state["winner"]
        
        # Clear existing units
        self.game.units = []
        
        # Deserialize units
        from boneglaive.utils.constants import UnitType
        for unit_data in state["units"]:
            unit_type = UnitType[unit_data["type"]]
            player = unit_data["player"]
            y = unit_data["position"]["y"]
            x = unit_data["position"]["x"]
            
            # Create new unit
            try:
                unit = self.game.add_unit(unit_type, player, y, x)
                if unit is None:
                    logger.warning(f"Failed to create unit {unit_type.name} at ({y}, {x}): add_unit returned None")
                    continue
            except ValueError as e:
                logger.warning(f"Failed to restore unit {unit_type.name} at ({y}, {x}): {e}")
                continue
            
            # Update unit properties
            unit.hp = unit_data["hp"]
            unit.max_hp = unit_data["max_hp"]
            unit.attack = unit_data["attack"]
            unit.defense = unit_data["defense"]
            unit.move_range = unit_data["move_range"]
            unit.attack_range = unit_data["attack_range"]
            unit.move_target = unit_data["move_target"]
            unit.attack_target = unit_data["attack_target"]
    
    def _handle_game_state(self, data: Dict[str, Any]) -> None:
        """
        OLD GAME STATE HANDLER - DISABLED for Phase 5
        This method conflicts with Phase 5 batch system - now using GAME_STATE_BATCH only
        """
        logger.warning("OLD_GAME_STATE_HANDLER: Received old-style GAME_STATE message - ignoring (Phase 5 uses GAME_STATE_BATCH)")
        return
    
    def send_player_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """
        Send a player action to the host.
        """
        my_player_num = self.network.get_player_number()
        is_host = self.network.is_host()
        current_game_player = self.game.current_player
        
        logger.info(f"SEND_ACTION DEBUG: {action_type} - my_player_num={my_player_num}, is_host={is_host}, current_game_player={current_game_player}")
        
        # BIDIRECTIONAL PROCESSING: Both players execute their own actions locally first
        # This ensures animations and effects play on the acting player's screen
        logger.info(f"LOCAL_ACTION_PROCESSING: {action_type} - executing locally first")
        
        if action_type != "end_turn":
            # For non-end-turn actions (move, attack), apply locally immediately
            # This gives instant feedback to the player
            self._apply_action(action_type, data)
            logger.info(f"LOCAL_ACTION_PROCESSING: Applied {action_type} locally for immediate feedback")
        
        # Host processes actions locally and that's it (no network sending to self)
        if self.network.is_host():
            logger.info(f"HOST_ACTION_PROCESSING: Host processed {action_type} locally")
            if action_type == "end_turn":
                # Host processes end_turn locally too
                self._apply_action(action_type, data)
            return
        
        # For client end_turn, execute turn locally FIRST, then send complete state
        if action_type == "end_turn":
            from boneglaive.utils.message_log import message_log
            
            # CLIENT LOCAL EXECUTION: Apply planned actions and execute turn locally first
            # This ensures Player 2 sees their own animations and effects
            logger.info(f"CLIENT_LOCAL_EXECUTION: Player 2 executing turn locally first")
            
            # Apply planned actions first
            planned_actions = data.get("planned_actions", [])
            if planned_actions:
                logger.info(f"CLIENT_LOCAL_EXECUTION: Applying {len(planned_actions)} planned actions locally")
                self._apply_planned_actions(planned_actions)
            
            # Execute turn locally with animations for Player 2
            if self.ui:
                logger.info(f"CLIENT_LOCAL_EXECUTION: Executing turn with animations for Player 2")
                self.game.execute_turn(self.ui)
            else:
                logger.info(f"CLIENT_LOCAL_EXECUTION: Executing turn without UI for Player 2") 
                self.game.execute_turn()
            
            logger.info(f"CLIENT_LOCAL_EXECUTION: Player 2 turn execution completed locally")
            
            # CLIENT LOCAL TURN TRANSITION: Handle turn transition locally after execution
            current_player = self.game.current_player
            logger.info(f"CLIENT_LOCAL_TRANSITION: Before transition - current_player={current_player}, turn={self.game.turn}")
            
            if current_player == 1:
                # Player 1 finished, switch to Player 2
                self.game.current_player = 2
            elif current_player == 2:
                # Player 2 finished, switch to Player 1 and increment turn
                self.game.current_player = 1
                self.game.turn += 1
            
            # Initialize the new player's turn
            self.game.initialize_next_player_turn()
            
            logger.info(f"CLIENT_LOCAL_TRANSITION: After transition - current_player={self.game.current_player}, turn={self.game.turn}")
            
            # Update UI for the client after local turn transition
            if self.ui:
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                
                # CRITICAL FIX: Ensure P2's messages are displayed before any UI state changes
                # Force immediate UI refresh to display P2's generated messages
                logger.info(f"P2_MESSAGE_FIX: Ensuring {len(message_log.messages)} messages are visible on P2's screen")
                
                # Force a complete UI redraw to ensure P2 sees their messages
                self.ui.draw_board()
                
                # Start collecting messages for the new turn
                message_log.start_new_turn()
                
                if self.game.current_player == self.network.get_player_number():
                    # Still my turn (shouldn't happen normally)
                    message_log.add_system_message(f"Your turn - Turn {self.game.turn}")
                    self.ui.message = f"Your turn - Turn {self.game.turn}"
                    logger.info(f"CLIENT_LOCAL_TRANSITION: UI updated - still my turn")
                else:
                    # Other player's turn
                    message_log.add_system_message(f"Player {self.game.current_player}'s turn - Turn {self.game.turn}")
                    self.ui.message = f"Player {self.game.current_player} is thinking..."
                    logger.info(f"CLIENT_LOCAL_TRANSITION: UI updated - other player's turn")
                
                # Update the player message in UI
                self.ui.update_player_message()
                
                # FINAL FIX: Force another UI redraw after all updates to ensure messages remain visible
                self.ui.draw_board()
                logger.info(f"P2_MESSAGE_FIX: Final UI redraw completed - P2's messages should now be visible")
            
            # Collect turn messages from client AFTER local execution
            turn_messages = message_log.get_turn_messages()
            
            # Serialize MessageType enums for network transmission
            serialized_messages = []
            for msg in turn_messages:
                serialized_msg = msg.copy()
                if 'type' in serialized_msg and hasattr(serialized_msg['type'], 'value'):
                    serialized_msg['type'] = serialized_msg['type'].value
                serialized_messages.append(serialized_msg)
            
            logger.info(f"CLIENT END_TURN DEBUG: Collected {len(turn_messages)} messages, sending to host")
            
            # Send turn messages to host before sending end_turn action
            if serialized_messages:
                # Generate checksum before sending
                checksum = message_log.get_message_log_checksum()
                
                message_batch_msg = {
                    "messages": serialized_messages,
                    "from_player": current_game_player,
                    "turn_number": self.game.turn,
                    "checksum": checksum,
                    "timestamp": time.time()
                }
                success = self.network.send_message(MessageType.MESSAGE_LOG_BATCH, message_batch_msg)
                if success:
                    logger.info(f"CLIENT END_TURN DEBUG: Sent {len(serialized_messages)} turn messages to host with checksum {checksum}")
                else:
                    logger.error(f"CLIENT END_TURN DEBUG: Failed to send turn messages to host")
                    return  # Don't proceed if message batch failed
                
                # Send complete game state to host for synchronization
                # This contains the RESULTS of Player 2's local execution
                game_state = game_state_serializer.serialize_game_state(self.game)
                state_checksum = game_state_serializer.generate_checksum(self.game)
                
                game_state_msg = {
                    "state": game_state,
                    "from_player": current_game_player,  # The player who just finished their turn
                    "turn_number": self.game.turn,  # Turn number after local transition
                    "checksum": state_checksum,
                    "already_executed": True,  # Flag that this turn was already executed locally
                    "turn_transitioned": True,  # Flag that turn transition was handled locally
                    "timestamp": time.time()
                }
                
                success = self.network.send_message(MessageType.GAME_STATE_BATCH, game_state_msg)
                if success:
                    logger.info(f"CLIENT END_TURN DEBUG: Sent complete game state to host with checksum {state_checksum}")
                else:
                    logger.error(f"CLIENT END_TURN DEBUG: Failed to send game state to host")
                    return  # Don't proceed if game state batch failed
                
                # Small delay to ensure batches are processed
                time.sleep(0.05)
        
        # Send action to host
        action_data = {
            "action_type": action_type,
            "data": data,
            "timestamp": time.time()
        }
        
        # Send action to host
        logger.info(f"SEND_ACTION DEBUG: Client sending {action_type} to host")
        self.network.send_message(MessageType.PLAYER_ACTION, action_data)
    
    def send_setup_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """
        Send a setup action to the host.
        """
        # Only allow setup actions if it's this player's turn
        if not self.can_act_in_setup():
            logger.warning(f"Attempted setup action {action_type} when not this player's turn")
            return
        
        # Host can apply setup actions directly
        if self.network.is_host():
            self._apply_setup_action(action_type, data)
            return
        
        # For clients, apply the action locally AND send to host
        # This allows the client to see their own units immediately
        self._apply_setup_action(action_type, data)
        
        # Send setup action to host
        self.network.send_message(MessageType.SETUP_ACTION, {
            "action_type": action_type,
            "data": data,
            "timestamp": time.time()
        })
    
    def _handle_player_action(self, data: Dict[str, Any]) -> None:
        """
        Handle received player action message.
        FIX: Process Player 2 actions immediately instead of queuing them.
        """
        # Only host should process player actions
        if not self.network.is_host():
            return
        
        try:
            action_type = data.get("action_type", "")
            action_data = data.get("data", {})
            timestamp = data.get("timestamp", 0)
            
            logger.info(f"P2_ACTION_FIX: Host received {action_type} from Player 2")
            
            # CRITICAL FIX: Apply Player 2 actions IMMEDIATELY instead of queuing
            # The old system queued actions and processed them in update() loop,
            # which caused timing issues and prevented proper turn execution
            
            if action_type == "end_turn":
                logger.info(f"P2_ACTION_FIX: Processing Player 2 end_turn immediately")
                
                # RACE CONDITION FIX: Check if the sender's turn was already completed via state batch
                current_turn = self.game.turn
                # The sender is the non-host player (Player 2)
                sending_player = 2  # Since only Player 2 sends actions to host
                
                # Check if this specific player's turn for this turn number was already completed
                if sending_player in self.completed_turn_states and self.completed_turn_states[sending_player] >= current_turn:
                    logger.info(f"RACE_CONDITION_FIX: Player {sending_player} turn {current_turn} already completed via state batch - skipping action processing")
                    # Clear any pending actions since the turn is already complete
                    if self.pending_actions:
                        logger.info(f"RACE_CONDITION_FIX: Clearing {len(self.pending_actions)} pending actions (already processed via state)")
                        self.pending_actions = []
                    return  # Skip processing the individual actions
                
                # Apply any queued actions first (move, attack, etc.)
                if self.pending_actions:
                    logger.info(f"P2_ACTION_FIX: Applying {len(self.pending_actions)} queued actions before end_turn")
                    for queued_action_type, queued_action_data, _ in self.pending_actions:
                        self._apply_action(queued_action_type, queued_action_data)
                    self.pending_actions = []  # Clear queue
                
                # Now apply the end_turn action
                self._apply_action(action_type, action_data)
                logger.info(f"P2_ACTION_FIX: Player 2 turn execution completed")
            else:
                # For non-end_turn actions, still queue them to be processed before end_turn
                logger.info(f"P2_ACTION_FIX: Queuing {action_type} action for batch processing")
                self.pending_actions.append((action_type, action_data, timestamp))
                # Sort by timestamp
                self.pending_actions.sort(key=lambda x: x[2])
            
        except Exception as e:
            logger.error(f"Error handling player action: {str(e)}")
    
    def _apply_pending_actions(self) -> None:
        """
        Apply any pending player actions.
        PHASE 5 NOTE: Old game state application disabled - now using GAME_STATE_BATCH system
        """
        # OLD GAME STATE APPLICATION DISABLED - Phase 5 uses batch system
        # This old code conflicts with Phase 5 game state batch handling
        # Game states now applied via _handle_game_state_batch() only
        if not self.network.is_host() and self.received_states:
            logger.warning("OLD_STATE_APPLICATION: Ignoring old received_states queue - using Phase 5 batch system")
            self.received_states = []  # Clear old queue to prevent interference
        
        # Apply pending actions (for host) - this part is still used
        if self.network.is_host() and self.pending_actions:
            for action_type, action_data, _ in self.pending_actions:
                self._apply_action(action_type, action_data)
            self.pending_actions = []
    
    def _apply_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """
        Apply a player action to the game state.
        """
        # Implement based on your game's action types
        if action_type == "move":
            unit_id = data.get("unit_id")
            target = data.get("target")
            
            # Find unit by ID
            for unit in self.game.units:
                if id(unit) == unit_id and unit.is_alive():
                    unit.move_target = target
                    # Mark that this unit is taking an action (won't regenerate HP)
                    unit.took_no_actions = False
                    # Track action order
                    unit.action_timestamp = self.game.action_counter
                    self.game.action_counter += 1
                    break
        
        elif action_type == "attack":
            unit_id = data.get("unit_id")
            target = data.get("target")
            
            # Find unit by ID
            for unit in self.game.units:
                if id(unit) == unit_id and unit.is_alive():
                    unit.attack_target = target
                    # Mark that this unit is taking an action (won't regenerate HP)
                    unit.took_no_actions = False
                    # Track action order
                    unit.action_timestamp = self.game.action_counter
                    self.game.action_counter += 1
                    break
        
        elif action_type == "end_turn":
            from boneglaive.utils.message_log import message_log
            
            # Apply planned actions and execute turn FIRST
            planned_actions = data.get("planned_actions", [])
            if planned_actions:
                self._apply_planned_actions(planned_actions)
            
            # Execute turn for all units with animations
            if self.ui:
                self.game.execute_turn(self.ui)
            else:
                self.game.execute_turn()
            
            # AFTER everything resolves, collect turn messages for network sync
            turn_messages = message_log.get_turn_messages()
            
            # Serialize MessageType enums for network transmission
            serialized_messages = []
            for msg in turn_messages:
                serialized_msg = msg.copy()
                if 'type' in serialized_msg and hasattr(serialized_msg['type'], 'value'):
                    serialized_msg['type'] = serialized_msg['type'].value
                serialized_messages.append(serialized_msg)
            
            logger.info(f"HOST END_TURN DEBUG: Collected {len(turn_messages)} messages after turn execution")
            
            # Handle turn transition after execution (only host)
            logger.info(f"P2_TURN_FIX: Checking if should handle turn transition - is_host={self.network.is_host()}")
            if self.network.is_host():
                current_turn = self.game.turn
                current_player = self.game.current_player
                transition_key = (current_turn, current_player)
                
                # DOUBLE TRANSITION PREVENTION: Only skip if THIS SPECIFIC player's turn transition was already processed via batch
                if transition_key in self.processed_turn_transitions:
                    logger.info(f"DOUBLE_TRANSITION_PREVENTION: Player {current_player} turn {current_turn} transition already processed via batch - skipping host transition")
                    return  # Don't process turn transition again
                
                logger.info(f"P2_TURN_FIX: Host handling turn transition")
                # Determine next player
                current_player = self.game.current_player
                next_player = 2 if current_player == 1 else 1
                
                logger.info(f"HOST END_TURN DEBUG: Before switch - current_player={current_player}, host_player_num={self.network.get_player_number()}")
                
                # Update game state
                if current_player == 1:
                    # Player 1 finished, switch to Player 2
                    logger.info(f"P2_TURN_FIX: Player 1 finished, switching to Player 2")
                    self.game.current_player = 2
                elif current_player == 2:
                    # Player 2 finished, switch to Player 1 and increment turn
                    logger.info(f"P2_TURN_FIX: Player 2 finished, switching to Player 1 and incrementing turn")
                    self.game.current_player = 1
                    self.game.turn += 1
                    
                    # RACE CONDITION FIX: Clean up old completed turn states when turn advances
                    self.cleanup_completed_turn_states(self.game.turn)
                else:
                    logger.warning(f"P2_TURN_FIX: Unexpected current_player value: {current_player}")
                
                logger.info(f"HOST END_TURN DEBUG: After switch - new_current_player={self.game.current_player}, turn={self.game.turn}")
                logger.info(f"P2_TURN_FIX: Turn transition completed - current_player={self.game.current_player}, turn={self.game.turn}")
                
                # Initialize the new player's turn
                self.game.initialize_next_player_turn()
                
                # Send turn messages to client (if there are any)
                if serialized_messages:
                    # Generate checksum after messages are added locally
                    checksum = message_log.get_message_log_checksum()
                    
                    message_batch_msg = {
                        "messages": serialized_messages,
                        "from_player": current_player,
                        "turn_number": self.game.turn,
                        "checksum": checksum,
                        "timestamp": time.time()
                    }
                    success = self.network.send_message(MessageType.MESSAGE_LOG_BATCH, message_batch_msg)
                    if success:
                        logger.info(f"HOST END_TURN DEBUG: Sent {len(serialized_messages)} turn messages to client with checksum {checksum}")
                    else:
                        logger.error(f"HOST END_TURN DEBUG: Failed to send turn messages - connection may be lost")
                        return  # Don't proceed with turn transition if message batch failed
                
                # Send complete game state to client for synchronization  
                game_state = game_state_serializer.serialize_game_state(self.game)
                state_checksum = game_state_serializer.generate_checksum(self.game)
                
                game_state_msg = {
                    "state": game_state,
                    "from_player": current_player,  # This is the player who ENDED their turn
                    "turn_number": self.game.turn,  # Turn number after transition
                    "checksum": state_checksum,
                    "already_executed": True,  # Host also executes locally first
                    "timestamp": time.time()
                }
                
                logger.info(f"P2_TURN_FIX: Sending game state - from_player={current_player}, game.current_player={self.game.current_player}, turn={self.game.turn}")
                
                success = self.network.send_message(MessageType.GAME_STATE_BATCH, game_state_msg)
                if success:
                    logger.info(f"HOST END_TURN DEBUG: Sent complete game state to client with checksum {state_checksum}")
                else:
                    logger.error(f"HOST END_TURN DEBUG: Failed to send game state - connection may be lost")
                    return  # Don't proceed if game state batch failed
                
                # Small delay to ensure batches are processed before turn transition
                time.sleep(0.1)
                
                # Send turn transition to client
                turn_transition_msg = {
                    "new_player": self.game.current_player,
                    "turn_number": self.game.turn,
                    "timestamp": time.time()
                }
                success = self.network.send_message(MessageType.TURN_TRANSITION, turn_transition_msg)
                if success:
                    logger.info(f"HOST END_TURN DEBUG: Sent TURN_TRANSITION message to client - new_player={self.game.current_player}")
                    logger.info(f"HOST END_TURN DEBUG: Full TURN_TRANSITION message: {turn_transition_msg}")
                else:
                    logger.error(f"HOST END_TURN DEBUG: Failed to send TURN_TRANSITION - connection may be lost")
                
                # Update UI for host and start new turn message collection
                if self.ui:
                    from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                    
                    # Start collecting messages for the new turn
                    message_log.start_new_turn()
                    
                    if self.game.current_player == self.network.get_player_number():
                        # Host's turn
                        message_log.add_system_message(f"Your turn - Turn {self.game.turn}")
                        self.ui.message = f"Your turn - Turn {self.game.turn}"
                        logger.info(f"HOST END_TURN DEBUG: Host's turn, started new message collection")
                    else:
                        # Client's turn
                        message_log.add_system_message(f"Player {self.game.current_player}'s turn - Turn {self.game.turn}")  
                        self.ui.message = f"Player {self.game.current_player} is thinking..."
                        logger.info(f"HOST END_TURN DEBUG: Client's turn, started new message collection")
        
        # Add more action types as needed
    
    def _handle_setup_action(self, data: Dict[str, Any]) -> None:
        """
        Handle received setup action message.
        Only the host should process setup actions.
        """
        if not self.network.is_host():
            return
        
        try:
            action_type = data.get("action_type", "")
            action_data = data.get("data", {})
            timestamp = data.get("timestamp", 0)
            
            # Apply the setup action directly
            self._apply_setup_action(action_type, action_data)
            
        except Exception as e:
            logger.error(f"Error handling setup action: {str(e)}")
    
    def _handle_setup_phase_transition(self, data: Dict[str, Any]) -> None:
        """
        Handle setup phase transition message.
        Only clients should receive this.
        """
        if self.network.is_host():
            return
        
        try:
            new_setup_player = data.get("setup_player", 1)
            logger.info(f"Setup phase transition: now player {new_setup_player}'s turn")
            
            # Update the local game state to match
            self.game.setup_player = new_setup_player
            
            # Add appropriate message to UI
            if self.ui:
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                if new_setup_player == self.network.get_player_number():
                    message_log.add_system_message("Your turn to place units")
                    self.ui.message = "Your turn to place units"
                else:
                    message_log.add_system_message(f"Player {new_setup_player} is placing units...")
                    self.ui.message = f"Player {new_setup_player} is placing units..."
            
        except Exception as e:
            logger.error(f"Error handling setup phase transition: {str(e)}")
    
    def _handle_setup_complete(self, data: Dict[str, Any]) -> None:
        """
        Handle setup complete message.
        Both players should receive this.
        """
        try:
            logger.info("Setup phase complete, game starting")
            
            # End setup phase
            self.game.setup_phase = False
            
            # Add game start message and initialize simple network batching
            if self.ui:
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                
                # Enable network mode for message collection
                message_log.enable_network_mode()
                
                # Add game start message
                if self.network.get_player_number() == 1:
                    message_log.add_system_message(f"Game starting - Player 1's turn")
                    self.ui.message = f"Game starting - Player 1's turn"
                    logger.info("SETUP_COMPLETE DEBUG: Player 1 starting, network mode enabled")
                else:
                    message_log.add_system_message(f"Game starting - Player 1's turn")
                    self.ui.message = f"Player 1 is thinking..."
                    logger.info("SETUP_COMPLETE DEBUG: Player 2 waiting, network mode enabled")
                
                # Update the player message in UI
                self.ui.update_player_message()
            
        except Exception as e:
            logger.error(f"Error handling setup complete: {str(e)}")
    
    def _apply_setup_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """
        Apply a setup action to the game state.
        """
        if action_type == "place_unit":
            y = data.get("y")
            x = data.get("x")
            unit_type_name = data.get("unit_type")
            
            if y is not None and x is not None and unit_type_name:
                from boneglaive.utils.constants import UnitType
                try:
                    unit_type = UnitType[unit_type_name]
                    result = self.game.place_setup_unit(y, x, unit_type)
                    logger.debug(f"Placed setup unit {unit_type_name} at ({y}, {x}): {result}")
                except (KeyError, ValueError) as e:
                    logger.error(f"Error placing setup unit: {str(e)}")
        
        elif action_type == "confirm_setup":
            # Store which player is confirming before calling confirm_setup
            confirming_player = self.game.setup_player
            
            # For network multiplayer, manually handle the setup confirmation logic
            # instead of using the game engine's logic which assumes local multiplayer
            self.game.setup_confirmed[confirming_player] = True
            logger.info(f"Setup confirmed for player {confirming_player}")
            
            if self.network.is_host():
                if confirming_player == 1:
                    # Player 1 confirmed, transition to Player 2
                    self.game.setup_player = 2
                    self.network.send_message(MessageType.SETUP_PHASE_TRANSITION, {
                        "setup_player": 2,
                        "timestamp": time.time()
                    })
                    logger.info("Sent setup phase transition to Player 2")
                    
                    # Update UI for host
                    if self.ui:
                        from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                        message_log.add_system_message("Player 2 is placing units...")
                        self.ui.message = "Player 2 is placing units..."
                
                elif confirming_player == 2:
                    # Player 2 confirmed, game starts
                    # Resolve any unit placement conflicts before the game starts
                    self.game._resolve_unit_placement_conflicts()
                    
                    # Assign Greek identification letters to units
                    self.game._assign_greek_identifiers()
                    
                    # Move FOWL_CONTRIVANCE units to nearest rails
                    self.game._move_fowl_contrivances_to_rails()
                    
                    # End setup phase
                    self.game.setup_phase = False
                    
                    self.network.send_message(MessageType.SETUP_COMPLETE, {
                        "timestamp": time.time()
                    })
                    logger.info("Sent setup complete message")
                    
                    # Apply setup complete locally
                    self._handle_setup_complete({})
        
        # Add more setup action types as needed
    
    def _apply_planned_actions(self, planned_actions):
        """Apply a list of planned actions from a player."""
        for unit_actions in planned_actions:
            # Apply move action if present
            if 'move' in unit_actions:
                move_data = unit_actions['move']
                self._apply_action("move", move_data)
            
            # Apply attack action if present  
            if 'attack' in unit_actions:
                attack_data = unit_actions['attack']
                self._apply_action("attack", attack_data)
            
            # Apply metadata if present
            if 'metadata' in unit_actions:
                metadata = unit_actions['metadata']
                unit_id = unit_actions.get('move', unit_actions.get('attack', {})).get('unit_id')
                
                if unit_id:
                    # Find and update unit metadata
                    for unit in self.game.units:
                        if id(unit) == unit_id and unit.is_alive():
                            unit.took_no_actions = metadata.get('took_no_actions', True)
                            unit.action_timestamp = metadata.get('action_timestamp', 0)
                            break
    
    def _handle_turn_transition(self, data: Dict[str, Any]) -> None:
        """
        Handle turn transition message.
        Both players should receive this to sync turn state.
        """
        try:
            new_player = data.get("new_player", 1)
            turn_number = data.get("turn_number", 1)
            my_player_number = self.network.get_player_number()
            is_host = self.network.is_host()
            
            logger.info(f"TURN_TRANSITION DEBUG: Received message - new_player={new_player}, turn={turn_number}, my_player_num={my_player_number}, is_host={is_host}")
            
            # Update local game state
            old_current_player = self.game.current_player
            self.game.current_player = new_player
            self.game.turn = turn_number
            
            logger.info(f"TURN_TRANSITION DEBUG: Updated local state - old_current_player={old_current_player} -> new_current_player={self.game.current_player}")
            
            # RACE CONDITION FIX: Clean up old completed turn states when turn transitions
            self.cleanup_completed_turn_states(turn_number)
            
            # Initialize the new player's turn locally
            self.game.initialize_next_player_turn()
            
            # Update UI and start new turn message collection
            if self.ui:
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                
                # Start collecting messages for the new turn
                message_log.start_new_turn()
                
                if new_player == self.network.get_player_number():
                    # It's my turn
                    message_log.add_system_message(f"Your turn - Turn {turn_number}")
                    self.ui.message = f"Your turn - Turn {turn_number}"
                    logger.info(f"TURN_TRANSITION DEBUG: UI updated - it's MY turn now, started new message collection")
                else:
                    # Not my turn
                    message_log.add_system_message(f"Player {new_player}'s turn - Turn {turn_number}")
                    self.ui.message = f"Player {new_player} is thinking..."
                    logger.info(f"TURN_TRANSITION DEBUG: UI updated - it's OTHER player's turn, started new message collection")
                
                # Update the player message in UI
                self.ui.update_player_message()
                
                # Publish turn started event for the new player
                from boneglaive.utils.event_system import get_event_manager, EventType, TurnEventData
                event_manager = get_event_manager()
                event_manager.publish(
                    EventType.TURN_STARTED,
                    TurnEventData(
                        player=new_player,
                        turn_number=turn_number
                    )
                )
            
        except Exception as e:
            logger.error(f"Error handling turn transition: {str(e)}")
    
    def _handle_turn_complete(self, data: Dict[str, Any]) -> None:
        """
        Handle turn complete message.
        This can be used for future turn validation/confirmation.
        """
        try:
            logger.info("Turn execution complete")
            # Future: Add turn completion validation logic here
            
        except Exception as e:
            logger.error(f"Error handling turn complete: {str(e)}")
    
    def _handle_message_log_batch(self, data: Dict[str, Any]) -> None:
        """
        Handle received message log batch from other player.
        Add the messages to the local log and perform parity checking.
        """
        try:
            messages = data.get("messages", [])
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            other_checksum = data.get("checksum", "")
            message_count = data.get("message_count", len(messages))
            
            logger.info(f"MESSAGE_LOG_BATCH: Received {len(messages)} messages from Player {from_player} turn {turn_number}")
            
            # Validate message batch integrity
            if message_count != len(messages):
                logger.warning(f"MESSAGE_BATCH_INTEGRITY: Expected {message_count} messages, received {len(messages)}")
            
            if messages:
                from boneglaive.utils.message_log import message_log
                
                # Record message count before adding
                messages_before = len(message_log.messages)
                
                # Add the messages
                message_log.add_network_messages(messages)
                
                # Verify messages were added correctly
                messages_after = len(message_log.messages)
                messages_added = messages_after - messages_before
                
                logger.info(f"MESSAGE_LOG_BATCH: Added {messages_added} network messages to log (total: {messages_after})")
                
                if messages_added == 0 and len(messages) > 0:
                    logger.warning(f"MESSAGE_BATCH_ISSUE: Received {len(messages)} messages but none were added - possible duplicates or errors")
            else:
                logger.info(f"MESSAGE_LOG_BATCH: No messages to process from Player {from_player}")
                
                # Perform parity check if checksum was provided
                if other_checksum:
                    # ROBUST PARITY CHECK: Compare checksums AFTER both sides have the same messages
                    # The other player's checksum represents their state BEFORE sending messages
                    # Our checksum represents our state AFTER receiving their messages
                    # These should only match if we had all their messages before receiving the batch
                    
                    # Calculate what our checksum SHOULD be after adding their messages
                    my_checksum = message_log.get_message_log_checksum()
                    
                    # For merge-based sync, we expect temporary mismatches during message exchange
                    # Only trigger full sync recovery if we detect major inconsistencies
                    parity_match = message_log.verify_parity(other_checksum, from_player)
                    
                    logger.info(f"PARITY_ANALYSIS: Received checksum {other_checksum} from Player {from_player}")
                    logger.info(f"PARITY_ANALYSIS: Our checksum after adding messages: {my_checksum}")
                    logger.info(f"PARITY_ANALYSIS: Temporary mismatch is expected in merge-based sync")
                    
                    # Send our current checksum back for bidirectional verification
                    parity_response = {
                        "checksum": my_checksum,
                        "from_player": self.network.get_player_number(),
                        "parity_match": parity_match,
                        "turn_number": turn_number,
                        "timestamp": time.time()
                    }
                    
                    self.network.send_message(MessageType.PARITY_CHECK, parity_response)
                    logger.info(f"PARITY_CHECK DEBUG: Sent checksum response {my_checksum}")
                    
                    # CRITICAL CHANGE: Don't immediately trigger sync recovery on mismatch
                    # Let the bidirectional parity system handle verification
                    if not parity_match:
                        logger.info(f"EXPECTED_MISMATCH: Checksum difference is normal during message exchange")
                        logger.info(f"PARITY_FLOW: Waiting for other player's parity response to complete verification")
            
        except Exception as e:
            logger.error(f"Error handling message log batch: {str(e)}")
    
    def _handle_parity_check(self, data: Dict[str, Any]) -> None:
        """
        Handle parity check response from other player.
        Verify that both players have matching message log checksums.
        """
        try:
            other_checksum = data.get("checksum", "")
            from_player = data.get("from_player", 0)
            parity_match = data.get("parity_match", False)
            turn_number = data.get("turn_number", 0)
            
            logger.info(f"PARITY_RESPONSE: Received from Player {from_player}: checksum={other_checksum}, their_match={parity_match}")
            
            if other_checksum:
                from boneglaive.utils.message_log import message_log
                my_checksum = message_log.get_message_log_checksum()
                
                # CONVERGENT PARITY VERIFICATION
                # After message exchange, both players should eventually have the same messages
                final_parity_match = (my_checksum == other_checksum)
                
                logger.info(f"CONVERGENT_PARITY: My checksum: {my_checksum}")
                logger.info(f"CONVERGENT_PARITY: Their checksum: {other_checksum}")
                logger.info(f"CONVERGENT_PARITY: Final match: {final_parity_match}")
                
                if final_parity_match:
                    logger.info(f"PARITY_SUCCESS: ✓ Message logs now synchronized with Player {from_player}")
                else:
                    # Only trigger recovery if both sides report persistent mismatch
                    if not parity_match:
                        logger.warning(f"PERSISTENT_MISMATCH: Both players report checksum mismatch - triggering recovery")
                        sync_request = {
                            "from_player": self.network.get_player_number(),
                            "turn_number": turn_number,
                            "timestamp": time.time(),
                            "reason": "persistent_bidirectional_mismatch"
                        }
                        self.network.send_message(MessageType.MESSAGE_LOG_SYNC_REQUEST, sync_request)
                    else:
                        logger.info(f"ASYMMETRIC_MISMATCH: Only one side reports mismatch - likely timing issue, allowing convergence")
            
        except Exception as e:
            logger.error(f"Error handling parity check: {str(e)}")
    
    def _handle_sync_request(self, data: Dict[str, Any]) -> None:
        """
        Handle request for full message log sync.
        Send our complete message log to the requesting player.
        """
        try:
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            
            logger.info(f"SYNC_REQUEST DEBUG: Player {from_player} requested full message log sync")
            
            from boneglaive.utils.message_log import message_log
            
            # Get our complete message log
            full_log = message_log.get_full_message_log()
            
            # Send the full log back
            sync_response = {
                "messages": full_log,
                "from_player": self.network.get_player_number(),
                "turn_number": turn_number,
                "message_count": len(full_log),
                "timestamp": time.time()
            }
            
            success = self.network.send_message(MessageType.MESSAGE_LOG_FULL_SYNC, sync_response)
            if success:
                logger.info(f"SYNC_REQUEST DEBUG: Sent full message log ({len(full_log)} messages) to Player {from_player}")
            else:
                logger.error(f"SYNC_REQUEST DEBUG: Failed to send full message log to Player {from_player}")
            
        except Exception as e:
            logger.error(f"Error handling sync request: {str(e)}")
    
    def _handle_full_sync(self, data: Dict[str, Any]) -> None:
        """
        Handle full message log sync from another player.
        Replace our message log with theirs to fix sync issues.
        """
        try:
            messages = data.get("messages", [])
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            message_count = data.get("message_count", 0)
            
            logger.warning(f"FULL_SYNC DEBUG: Received full message log ({len(messages)} messages) from Player {from_player}")
            
            if messages:
                from boneglaive.utils.message_log import message_log
                
                # Replace our entire message log
                message_log.replace_message_log(messages)
                
                logger.warning(f"FULL_SYNC DEBUG: Successfully replaced message log with {len(messages)} messages")
                
                # Verify the sync worked by comparing checksums
                new_checksum = message_log.get_message_log_checksum()
                logger.info(f"FULL_SYNC DEBUG: New message log checksum after sync: {new_checksum}")
            
        except Exception as e:
            logger.error(f"Error handling full sync: {str(e)}")
    
    def _handle_game_state_batch(self, data: Dict[str, Any]) -> None:
        """
        Handle received game state batch from other player.
        Phase 5.6: BIDIRECTIONAL verification and cross-validation.
        
        This implements the same pattern as message log batching:
        1. Receive and apply the other player's state
        2. Send our own state back for cross-verification  
        3. Perform parity checks both ways
        4. Trigger reconciliation if needed
        """
        try:
            state_data = data.get("state", {})
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            other_checksum = data.get("checksum", "")
            my_player_num = self.network.get_player_number()
            is_cross_verification = data.get("cross_verification", False)
            already_executed = data.get("already_executed", False)
            turn_transitioned = data.get("turn_transitioned", False)
            
            logger.info(f"BIDIRECTIONAL_STATE_BATCH: Received game state from player {from_player} turn {turn_number} (cross_verification: {is_cross_verification}, already_executed: {already_executed}, turn_transitioned: {turn_transitioned})")
            logger.info(f"BIDIRECTIONAL_STATE_BATCH: My player num: {my_player_num}")
            
            if state_data and other_checksum:
                # Generate our current game state checksum BEFORE applying received state
                my_checksum_before = game_state_serializer.generate_checksum(self.game)
                
                logger.info(f"BIDIRECTIONAL_STATE_APPLY: Applying game state from player {from_player}")
                logger.info(f"BIDIRECTIONAL_STATE_APPLY: My checksum before: {my_checksum_before}")
                logger.info(f"BIDIRECTIONAL_STATE_APPLY: Their checksum: {other_checksum}")
                
                # Apply the received game state to our game
                try:
                    game_state_serializer.deserialize_game_state(state_data, self.game)
                    logger.info(f"BIDIRECTIONAL_STATE_APPLY: ✓ Game state successfully applied from player {from_player}")
                    
                    # RACE CONDITION FIX: Mark this player's turn as completed via state batch
                    # This prevents double-processing when the corresponding PLAYER_ACTION arrives
                    self.completed_turn_states[from_player] = turn_number
                    logger.info(f"RACE_CONDITION_FIX: Marked Player {from_player} turn {turn_number} as completed via state batch")
                    
                    # BIDIRECTIONAL EXECUTION FLAG: If the sender already executed locally, 
                    # we don't need to handle turn transitions on our side
                    if already_executed:
                        logger.info(f"BIDIRECTIONAL_EXECUTION: Player {from_player} already executed locally - applying final state only")
                        # The turn was fully executed by the sender, we just apply the final result
                        # No need to do turn transitions or execution logic on our side
                        
                        if turn_transitioned:
                            logger.info(f"BIDIRECTIONAL_TRANSITION: Player {from_player} already handled turn transition - updating UI only")
                            
                            # Mark this specific player's turn transition as processed
                            transition_key = (turn_number, from_player)
                            self.processed_turn_transitions[transition_key] = True
                            logger.info(f"TURN_TRANSITION_TRACKING: Marked Player {from_player} turn {turn_number} transition as processed via batch")
                            
                            # Update our UI to match the new turn state
                            if self.ui:
                                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                                
                                # Start collecting messages for the new turn
                                message_log.start_new_turn()
                                
                                if self.game.current_player == my_player_num:
                                    # It's now our turn
                                    message_log.add_system_message(f"Your turn - Turn {self.game.turn}")
                                    self.ui.message = f"Your turn - Turn {self.game.turn}"
                                    logger.info(f"BIDIRECTIONAL_TRANSITION: UI updated - now my turn")
                                else:
                                    # Still other player's turn
                                    message_log.add_system_message(f"Player {self.game.current_player}'s turn - Turn {self.game.turn}")
                                    self.ui.message = f"Player {self.game.current_player} is thinking..."
                                    logger.info(f"BIDIRECTIONAL_TRANSITION: UI updated - other player's turn")
                                
                                # Update the player message in UI
                                self.ui.update_player_message()
                    
                    # Verify the application worked by checking new checksum
                    my_checksum_after = game_state_serializer.generate_checksum(self.game)
                    parity_match = my_checksum_after == other_checksum
                    
                    logger.info(f"BIDIRECTIONAL_STATE_APPLY: My checksum after: {my_checksum_after}")
                    logger.info(f"BIDIRECTIONAL_STATE_APPLY: Parity match after apply: {parity_match}")
                    
                    # ===== BIDIRECTIONAL CROSS-VERIFICATION =====
                    # Send our complete game state back for bidirectional verification
                    # This mirrors the message log pattern where both sides send their data
                    # ONLY do this if it's not already a cross-verification message to avoid infinite loops
                    
                    if not is_cross_verification:
                        logger.info(f"BIDIRECTIONAL_CROSS_VERIFY: Sending our game state to player {from_player} for cross-verification")
                        
                        # Serialize our current game state
                        our_complete_state = game_state_serializer.serialize_game_state(self.game)
                        our_state_checksum = game_state_serializer.generate_checksum(self.game)
                        
                        # Send our game state back for bidirectional verification
                        cross_verify_batch = {
                            "state": our_complete_state,
                            "checksum": our_state_checksum,
                            "from_player": my_player_num,
                            "turn_number": turn_number,
                            "cross_verification": True,  # Flag to indicate this is cross-verification
                            "timestamp": time.time()
                        }
                        
                        cross_verify_sent = self.network.send_message(MessageType.GAME_STATE_BATCH, cross_verify_batch)
                        
                        if cross_verify_sent:
                            logger.info(f"BIDIRECTIONAL_CROSS_VERIFY: ✓ Sent our game state for cross-verification (checksum: {our_state_checksum})")
                        else:
                            logger.warning(f"BIDIRECTIONAL_CROSS_VERIFY: Failed to send cross-verification batch")
                    else:
                        logger.info(f"BIDIRECTIONAL_CROSS_VERIFY: Received cross-verification batch - no further cross-verification needed")
                    
                    # Send parity check response with bidirectional info
                    parity_response = {
                        "my_checksum": my_checksum_after,
                        "their_checksum": other_checksum,
                        "from_player": my_player_num,
                        "parity_match": parity_match,
                        "turn_number": turn_number,
                        "bidirectional_sync": True,  # Flag for bidirectional sync
                        "timestamp": time.time()
                    }
                    
                    self.network.send_message(MessageType.GAME_STATE_PARITY_CHECK, parity_response)
                    logger.info(f"BIDIRECTIONAL_PARITY: Sent bidirectional parity response (match: {parity_match})")
                    
                    # If there's still a mismatch after applying, use recovery system
                    if not parity_match:
                        logger.warning(f"BIDIRECTIONAL_RECOVERY: State mismatch persists after apply - using recovery")
                        self.handle_state_desync(other_checksum, from_player, turn_number)
                    else:
                        # Successfully synchronized!
                        logger.info(f"BIDIRECTIONAL_STATE_APPLY: ✓ Game state successfully synchronized with player {from_player}")
                        
                except Exception as apply_error:
                    logger.error(f"BIDIRECTIONAL_STATE_APPLY ERROR: Failed to apply game state: {str(apply_error)}")
                    # Use recovery system if direct application fails
                    self.handle_state_desync(other_checksum, from_player, turn_number)
                
        except Exception as e:
            logger.error(f"Error handling bidirectional game state batch: {str(e)}")
    
    def _handle_game_state_parity_check(self, data: Dict[str, Any]) -> None:
        """
        Handle parity check response for game state.
        Trigger recovery if parity mismatch is confirmed.
        """
        try:
            my_checksum = data.get("my_checksum", "")
            their_checksum = data.get("their_checksum", "")
            from_player = data.get("from_player", 0)
            parity_match = data.get("parity_match", False)
            turn_number = data.get("turn_number", 0)
            
            logger.info(f"GAME_STATE_PARITY_RESPONSE DEBUG: From player {from_player} - match: {parity_match}")
            
            # Verify parity from our side as well
            current_checksum = game_state_serializer.generate_checksum(self.game)
            our_parity_match = current_checksum == their_checksum
            
            # Final parity result
            if parity_match and our_parity_match:
                logger.info(f"GAME_STATE_PARITY RESULT: ✓ Game states are in perfect sync after turn {turn_number}")
            else:
                logger.warning(f"GAME_STATE_PARITY RESULT: ✗ Game state sync issue detected after turn {turn_number}")
                logger.warning(f"Their verification: {parity_match}, My verification: {our_parity_match}")
                
                # Use structured recovery system to fix the issue
                logger.warning(f"GAME_STATE_RECOVERY: Using structured recovery system")
                self.handle_state_desync(their_checksum, from_player, turn_number)
                
        except Exception as e:
            logger.error(f"Error handling game state parity check: {str(e)}")
    
    def _handle_game_state_sync_request(self, data: Dict[str, Any]) -> None:
        """
        Handle request for full game state sync.
        Send our complete game state to the requesting player.
        """
        try:
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            
            logger.warning(f"GAME_STATE_SYNC_REQUEST DEBUG: Player {from_player} requested full game state sync")
            
            # Serialize our complete game state
            full_state = game_state_serializer.serialize_game_state(self.game)
            state_checksum = game_state_serializer.generate_checksum(self.game)
            
            # Send the full state back
            sync_response = {
                "state": full_state,
                "checksum": state_checksum,
                "from_player": self.network.get_player_number(),
                "turn_number": turn_number,
                "timestamp": time.time()
            }
            
            success = self.network.send_message(MessageType.GAME_STATE_FULL_SYNC, sync_response)
            if success:
                logger.warning(f"GAME_STATE_SYNC_REQUEST DEBUG: Sent full game state to Player {from_player} (checksum: {state_checksum})")
            else:
                logger.error(f"GAME_STATE_SYNC_REQUEST DEBUG: Failed to send full game state to Player {from_player}")
            
        except Exception as e:
            logger.error(f"Error handling game state sync request: {str(e)}")
    
    def _handle_game_state_full_sync(self, data: Dict[str, Any]) -> None:
        """
        Handle full game state sync from another player.
        Phase 5.6: Enhanced bidirectional full sync with authority handling.
        Replace our game state with theirs to fix sync issues.
        """
        try:
            state_data = data.get("state", {})
            other_checksum = data.get("checksum", "")
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            is_authoritative = data.get("authoritative", False)
            
            logger.warning(f"BIDIRECTIONAL_FULL_SYNC DEBUG: Received full game state from Player {from_player} (authoritative: {is_authoritative})")
            
            if state_data and other_checksum:
                # Use structured recovery system with UI preservation
                recovery_success = self.replace_game_state_with_recovery(
                    state_data, other_checksum, from_player, is_authoritative
                )
                
                if not recovery_success:
                    logger.error(f"BIDIRECTIONAL_RECOVERY: ✗ Structured recovery failed for Player {from_player}")
                    # Could implement additional fallback mechanisms here if needed
                else:
                    logger.warning(f"BIDIRECTIONAL_RECOVERY: ✓ Successfully recovered game state from Player {from_player}")
            
        except Exception as e:
            logger.error(f"Error handling bidirectional game state full sync: {str(e)}")
    
    # ===== PHASE 5.4: GAME STATE BATCH SENDING METHODS =====
    
    def send_game_state_batch(self, turn_number: Optional[int] = None) -> bool:
        """
        Send complete game state batch to other player at turn end.
        Phase 5.4: Core game state synchronization pattern.
        """
        try:
            if turn_number is None:
                turn_number = self.game.turn
                
            logger.info(f"GAME_STATE_BATCH_SEND: Sending game state batch for turn {turn_number}")
            
            # Serialize complete game state
            complete_state = game_state_serializer.serialize_game_state(self.game)
            state_checksum = game_state_serializer.generate_checksum(self.game)
            
            # Prepare batch message
            batch_data = {
                "state": complete_state,
                "checksum": state_checksum,
                "from_player": self.network.get_player_number(),
                "turn_number": turn_number,
                "timestamp": time.time()
            }
            
            # Send to other player
            success = self.network.send_message(MessageType.GAME_STATE_BATCH, batch_data)
            
            if success:
                logger.info(f"GAME_STATE_BATCH_SEND: ✓ Sent game state batch (checksum: {state_checksum})")
                return True
            else:
                logger.error(f"GAME_STATE_BATCH_SEND: ✗ Failed to send game state batch")
                return False
                
        except Exception as e:
            logger.error(f"Error sending game state batch: {str(e)}")
            return False
    
    def send_game_state_parity_check(self, their_checksum: str, turn_number: Optional[int] = None) -> bool:
        """
        Send parity check response comparing our checksum with theirs.
        Phase 5.4: Bidirectional state verification.
        """
        try:
            if turn_number is None:
                turn_number = self.game.turn
                
            logger.info(f"GAME_STATE_PARITY_SEND: Sending parity check for turn {turn_number}")
            
            # Generate our current checksum
            my_checksum = game_state_serializer.generate_checksum(self.game)
            parity_match = my_checksum == their_checksum
            
            # Prepare parity check response
            parity_data = {
                "my_checksum": my_checksum,
                "their_checksum": their_checksum,
                "parity_match": parity_match,
                "from_player": self.network.get_player_number(),
                "turn_number": turn_number,
                "timestamp": time.time()
            }
            
            # Send parity check
            success = self.network.send_message(MessageType.GAME_STATE_PARITY_CHECK, parity_data)
            
            if success:
                logger.info(f"GAME_STATE_PARITY_SEND: ✓ Sent parity check (match: {parity_match})")
                return True
            else:
                logger.error(f"GAME_STATE_PARITY_SEND: ✗ Failed to send parity check")
                return False
                
        except Exception as e:
            logger.error(f"Error sending game state parity check: {str(e)}")
            return False
    
    def perform_end_of_turn_sync(self) -> bool:
        """
        Perform complete end-of-turn game state synchronization.
        Phase 5.6: BIDIRECTIONAL sync integration pattern.
        
        This method implements bidirectional game state sync similar to message log:
        - Both players send their complete game state
        - Both players receive and verify the other's state
        - Both perform parity checks and trigger reconciliation if needed
        
        This method should be called after all turn effects are resolved
        but before transitioning to the next player's turn.
        """
        try:
            current_turn = self.game.turn
            current_player = self.game.current_player
            my_player_num = self.network.get_player_number()
            
            logger.info(f"BIDIRECTIONAL_SYNC: Starting turn {current_turn} player {current_player} bidirectional sync")
            logger.info(f"BIDIRECTIONAL_SYNC: My network player number: {my_player_num}")
            
            # ===== BIDIRECTIONAL GAME STATE EXCHANGE =====
            # Both players send their complete game state, similar to message log pattern
            
            # 1. Send our complete game state to other player
            batch_sent = self.send_game_state_batch(current_turn)
            
            if not batch_sent:
                logger.warning(f"BIDIRECTIONAL_SYNC: Failed to send game state batch - sync incomplete")
                return False
            
            logger.info(f"BIDIRECTIONAL_SYNC: ✓ Sent our game state batch for turn {current_turn}")
            
            # 2. The other player will also send their game state via _handle_game_state_batch
            #    This creates a bidirectional exchange where both players send and receive states
            #    and both perform parity verification against each other
            
            logger.info(f"BIDIRECTIONAL_SYNC: ✓ Turn {current_turn} bidirectional sync initiated successfully")
            logger.info(f"BIDIRECTIONAL_SYNC: Waiting for other player's game state batch for cross-verification...")
            return True
            
        except Exception as e:
            logger.error(f"Error in bidirectional end-of-turn sync: {str(e)}")
            return False
    
    # ===== PHASE 5.5: RECOVERY & ERROR HANDLING METHODS =====
    
    def handle_state_desync(self, other_checksum: str, from_player: int, turn_number: int) -> bool:
        """
        Handle detected game state desync by requesting authoritative state.
        Phase 5.6: Enhanced bidirectional desync detection and recovery.
        """
        try:
            my_checksum = game_state_serializer.generate_checksum(self.game)
            my_player_num = self.network.get_player_number()
            
            logger.warning(f"BIDIRECTIONAL_DESYNC_HANDLER: Game state desync detected!")
            logger.warning(f"  Turn: {turn_number}, From Player: {from_player}")
            logger.warning(f"  My player number: {my_player_num}")
            logger.warning(f"  My checksum: {my_checksum}")
            logger.warning(f"  Their checksum: {other_checksum}")
            
            # In bidirectional sync, determine authority based on network role
            # Host (Player 1) is typically authoritative, but we implement mutual recovery
            if self.network.is_host():
                logger.warning(f"BIDIRECTIONAL_DESYNC: As host, sending our authoritative state to player {from_player}")
                # Host sends their state as authoritative
                return self.send_authoritative_game_state_sync(from_player, turn_number)
            else:
                logger.warning(f"BIDIRECTIONAL_DESYNC: As client, requesting authoritative state from host (player {from_player})")
                # Client requests authoritative state from host
                return self.request_full_game_state_sync(from_player, turn_number)
            
        except Exception as e:
            logger.error(f"Error handling bidirectional state desync: {str(e)}")
            return False
    
    def send_authoritative_game_state_sync(self, to_player: int, turn_number: int) -> bool:
        """
        Send our game state as the authoritative version for desync resolution.
        Phase 5.6: Bidirectional authority resolution.
        """
        try:
            logger.warning(f"AUTHORITATIVE_SYNC: Sending authoritative game state to player {to_player}")
            
            # Serialize our complete game state as authoritative
            authoritative_state = game_state_serializer.serialize_game_state(self.game)
            authoritative_checksum = game_state_serializer.generate_checksum(self.game)
            
            # Send as full sync message
            auth_sync_data = {
                "state": authoritative_state,
                "checksum": authoritative_checksum,
                "from_player": self.network.get_player_number(),
                "turn_number": turn_number,
                "authoritative": True,  # Flag this as authoritative
                "timestamp": time.time()
            }
            
            success = self.network.send_message(MessageType.GAME_STATE_FULL_SYNC, auth_sync_data)
            
            if success:
                logger.warning(f"AUTHORITATIVE_SYNC: ✓ Sent authoritative game state (checksum: {authoritative_checksum})")
                return True
            else:
                logger.error(f"AUTHORITATIVE_SYNC: Failed to send authoritative game state")
                return False
                
        except Exception as e:
            logger.error(f"Error sending authoritative game state sync: {str(e)}")
            return False
    
    def request_full_game_state_sync(self, from_player: int, turn_number: int) -> bool:
        """
        Request complete game state from another player for recovery.
        Phase 5.5: Structured sync request with error handling.
        """
        try:
            logger.warning(f"SYNC_REQUEST: Requesting full game state from Player {from_player}")
            
            sync_request = {
                "from_player": self.network.get_player_number(),
                "target_player": from_player,
                "turn_number": turn_number,
                "timestamp": time.time(),
                "reason": "checksum_mismatch"
            }
            
            success = self.network.send_message(MessageType.GAME_STATE_SYNC_REQUEST, sync_request)
            
            if success:
                logger.warning(f"SYNC_REQUEST: ✓ Full state sync request sent to Player {from_player}")
                return True
            else:
                logger.error(f"SYNC_REQUEST: ✗ Failed to send sync request to Player {from_player}")
                return False
                
        except Exception as e:
            logger.error(f"Error requesting full game state sync: {str(e)}")
            return False
    
    def replace_game_state_with_recovery(self, authoritative_state: Dict[str, Any], 
                                       expected_checksum: str, from_player: int, is_authoritative: bool = False) -> bool:
        """
        Replace entire game state with authoritative version, preserving UI state.
        Phase 5.6: Enhanced bidirectional state recovery with authority handling.
        """
        try:
            authority_text = "authoritative" if is_authoritative else "recovery"
            logger.warning(f"BIDIRECTIONAL_STATE_REPLACEMENT: Starting full game state {authority_text} recovery from Player {from_player}")
            
            # Store current state for rollback if needed
            old_checksum = game_state_serializer.generate_checksum(self.game)
            
            # Preserve UI state during recovery
            ui_state = self.preserve_ui_state()
            
            # Replace complete game state
            logger.warning(f"STATE_REPLACEMENT: Applying authoritative game state...")
            game_state_serializer.deserialize_game_state(authoritative_state, self.game)
            
            # Verify the replacement worked
            new_checksum = game_state_serializer.generate_checksum(self.game)
            
            logger.warning(f"STATE_REPLACEMENT: Recovery verification:")
            logger.warning(f"  Old checksum: {old_checksum}")
            logger.warning(f"  Expected: {expected_checksum}")
            logger.warning(f"  New checksum: {new_checksum}")
            
            if new_checksum == expected_checksum:
                # Restore UI state after successful replacement
                self.restore_ui_state(ui_state)
                
                # Add system message about recovery
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                message_log.add_message(
                    f"Game state synchronized with Player {from_player}",
                    LogMessageType.SYSTEM
                )
                
                logger.info(f"STATE_REPLACEMENT: ✓ Game state successfully recovered from Player {from_player}")
                return True
            else:
                logger.error(f"STATE_REPLACEMENT: ✗ State recovery failed - checksum mismatch persists")
                logger.error(f"  Expected: {expected_checksum}, Got: {new_checksum}")
                
                # Restore UI state even on failure
                self.restore_ui_state(ui_state)
                return False
                
        except Exception as e:
            logger.error(f"Error replacing game state: {str(e)}")
            # Try to restore UI state on exception
            try:
                if 'ui_state' in locals():
                    self.restore_ui_state(ui_state)
            except:
                pass
            return False
    
    def preserve_ui_state(self) -> Dict[str, Any]:
        """
        Preserve UI state that should survive game state recovery.
        Phase 5.5: UI state preservation during recovery.
        """
        ui_state = {}
        
        try:
            # Preserve UI reference if available
            if hasattr(self, 'ui') and self.ui:
                ui_state['ui_reference'] = self.ui
                
                # Preserve current UI mode/state
                if hasattr(self.ui, 'current_mode'):
                    ui_state['current_mode'] = self.ui.current_mode
                
                # Preserve selected unit/cursor position
                if hasattr(self.ui, 'selected_unit'):
                    ui_state['selected_unit_id'] = getattr(self.ui.selected_unit, 'greek_id', None)
                
                if hasattr(self.ui, 'cursor_y') and hasattr(self.ui, 'cursor_x'):
                    ui_state['cursor_position'] = (self.ui.cursor_y, self.ui.cursor_x)
                
                # Preserve any active UI indicators
                if hasattr(self.ui, 'active_indicators'):
                    ui_state['active_indicators'] = copy.deepcopy(self.ui.active_indicators)
            
            # Preserve multiplayer manager state
            if self.multiplayer_manager:
                ui_state['multiplayer_manager'] = self.multiplayer_manager
            
            logger.debug(f"UI_PRESERVATION: Preserved {len(ui_state)} UI state components")
            return ui_state
            
        except Exception as e:
            logger.error(f"Error preserving UI state: {str(e)}")
            return {}
    
    def restore_ui_state(self, ui_state: Dict[str, Any]) -> None:
        """
        Restore UI state after game state recovery.
        Phase 5.5: UI state restoration after recovery.
        """
        try:
            if not ui_state:
                logger.debug("UI_RESTORATION: No UI state to restore")
                return
            
            # Restore UI reference
            if 'ui_reference' in ui_state and ui_state['ui_reference']:
                self.ui = ui_state['ui_reference']
                
                # Restore UI mode
                if 'current_mode' in ui_state and hasattr(self.ui, 'current_mode'):
                    self.ui.current_mode = ui_state['current_mode']
                
                # Restore selected unit by ID
                if 'selected_unit_id' in ui_state and ui_state['selected_unit_id']:
                    selected_id = ui_state['selected_unit_id']
                    for unit in self.game.units:
                        if unit.greek_id == selected_id:
                            if hasattr(self.ui, 'selected_unit'):
                                self.ui.selected_unit = unit
                            break
                
                # Restore cursor position
                if 'cursor_position' in ui_state:
                    cursor_y, cursor_x = ui_state['cursor_position']
                    if hasattr(self.ui, 'cursor_y'):
                        self.ui.cursor_y = cursor_y
                    if hasattr(self.ui, 'cursor_x'):
                        self.ui.cursor_x = cursor_x
                
                # Restore active indicators
                if 'active_indicators' in ui_state and hasattr(self.ui, 'active_indicators'):
                    self.ui.active_indicators = ui_state['active_indicators']
            
            # Restore multiplayer manager
            if 'multiplayer_manager' in ui_state:
                self.multiplayer_manager = ui_state['multiplayer_manager']
            
            logger.debug(f"UI_RESTORATION: Restored {len(ui_state)} UI state components")
            
        except Exception as e:
            logger.error(f"Error restoring UI state: {str(e)}")
    
    def detect_and_handle_network_errors(self) -> bool:
        """
        Detect and handle various network error conditions.
        Phase 5.5: Comprehensive network error handling.
        """
        try:
            # Check network interface status
            if not self.network or not hasattr(self.network, 'connected'):
                logger.warning("NETWORK_ERROR: No network interface available")
                return False
            
            if not self.network.connected:
                logger.warning("NETWORK_ERROR: Network connection lost")
                
                # Add system message about network issues
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                message_log.add_message(
                    "Network connection lost - attempting to reconnect...",
                    LogMessageType.SYSTEM
                )
                
                # Attempt reconnection if interface supports it
                if hasattr(self.network, 'reconnect'):
                    try:
                        reconnect_success = self.network.reconnect()
                        if reconnect_success:
                            message_log.add_message(
                                "Network connection restored",
                                LogMessageType.SYSTEM
                            )
                            logger.info("NETWORK_RECOVERY: Connection successfully restored")
                            return True
                    except Exception as reconnect_error:
                        logger.error(f"NETWORK_RECOVERY: Reconnection failed: {str(reconnect_error)}")
                
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in network error detection: {str(e)}")
            return False
    
    def set_ui_reference(self, ui) -> None:
        """
        Set UI reference for recovery operations.
        Phase 5.5: UI integration for recovery.
        """
        self.ui = ui
        logger.debug("UI_INTEGRATION: UI reference set for game state sync")
    
    def cleanup_completed_turn_states(self, current_turn: int) -> None:
        """
        Clean up old completed turn state tracking.
        Called during turn transitions to prevent stale state.
        """
        # Remove entries for turns that are now old
        to_remove = []
        for player, completed_turn in self.completed_turn_states.items():
            if completed_turn < current_turn:
                to_remove.append(player)
        
        for player in to_remove:
            del self.completed_turn_states[player]
            logger.debug(f"CLEANUP: Removed completed turn state for Player {player}")
        
        if to_remove:
            logger.info(f"CLEANUP: Cleaned up {len(to_remove)} old completed turn states")
        
        # Clean up old processed turn transitions
        transitions_to_remove = []
        for (turn_num, player) in self.processed_turn_transitions.keys():
            if turn_num < current_turn - 1:  # Keep current and previous turn
                transitions_to_remove.append((turn_num, player))
        
        for transition_key in transitions_to_remove:
            del self.processed_turn_transitions[transition_key]
            turn_num, player = transition_key
            logger.debug(f"CLEANUP: Removed processed transition for Player {player} turn {turn_num}")
        
        if transitions_to_remove:
            logger.info(f"CLEANUP: Cleaned up {len(transitions_to_remove)} old processed turn transitions")
    
    def update_with_error_handling(self) -> None:
        """
        Enhanced update method with comprehensive error handling.
        Phase 5.5: Integrated error detection and recovery.
        """
        try:
            # Check for network errors
            network_ok = self.detect_and_handle_network_errors()
            
            if network_ok:
                # Perform regular network message processing
                if hasattr(self.network, 'receive_messages'):
                    self.network.receive_messages()
            
        except Exception as e:
            logger.error(f"Error in enhanced update cycle: {str(e)}")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """
        Get current recovery and synchronization status.
        Phase 5.5: Status monitoring for debugging.
        """
        try:
            status = {
                "network_connected": False,
                "last_sync_time": self.last_sync_time,
                "game_checksum": None,
                "recovery_active": False
            }
            
            if self.network and hasattr(self.network, 'connected'):
                status["network_connected"] = self.network.connected
            
            if self.game:
                status["game_checksum"] = game_state_serializer.generate_checksum(self.game)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting recovery status: {str(e)}")
            return {"error": str(e)}