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
        
        # Register message handlers
        self.network.register_message_handler(
            MessageType.GAME_STATE, self._handle_game_state
        )
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
        current_time = time.time()
        if (self.network.is_host() and 
            current_time - self.last_sync_time >= self.sync_interval):
            self._sync_game_state()
            self.last_sync_time = current_time
    
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
        Convert game state to a serializable dictionary.
        """
        state = {
            "turn": self.game.turn,
            "current_player": self.game.current_player,
            "winner": self.game.winner,
            "units": []
        }
        
        # Serialize units
        for unit in self.game.units:
            if unit.is_alive():
                unit_data = {
                    "type": unit.type.name,
                    "player": unit.player,
                    "position": {"y": unit.y, "x": unit.x},
                    "hp": unit.hp,
                    "max_hp": unit.max_hp,
                    "attack": unit.attack,
                    "defense": unit.defense,
                    "move_range": unit.move_range,
                    "attack_range": unit.attack_range,
                    "move_target": unit.move_target,
                    "attack_target": unit.attack_target
                }
                state["units"].append(unit_data)
        
        return state
    
    def _deserialize_game_state(self, state: Dict[str, Any]) -> None:
        """
        Apply a serialized game state to the game.
        """
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
        Handle received game state message.
        """
        # Only non-host players should apply received game state
        if self.network.is_host():
            return
        
        try:
            state = data.get("state", {})
            timestamp = data.get("timestamp", 0)
            
            # Queue the state to be applied
            self.received_states.append((state, timestamp))
            
            # Sort by timestamp
            self.received_states.sort(key=lambda x: x[1])
            
        except Exception as e:
            logger.error(f"Error handling game state: {str(e)}")
    
    def send_player_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """
        Send a player action to the host.
        """
        my_player_num = self.network.get_player_number()
        is_host = self.network.is_host()
        current_game_player = self.game.current_player
        
        logger.info(f"SEND_ACTION DEBUG: {action_type} - my_player_num={my_player_num}, is_host={is_host}, current_game_player={current_game_player}")
        
        # Only non-host players need to send actions
        if self.network.is_host():
            # Host can apply actions directly
            logger.info(f"SEND_ACTION DEBUG: Host applying {action_type} directly")
            self._apply_action(action_type, data)
            return
        
        # For end_turn actions, include the client's message batch
        action_data = {
            "action_type": action_type,
            "data": data,
            "timestamp": time.time()
        }
        
        if action_type == "end_turn":
            # Collect client's message batch and include it
            from boneglaive.utils.message_log import message_log
            if message_log.is_batching:
                client_messages = message_log.end_turn_batch()
                
                # Chat messages are already included in client_messages via batching
                # No need for separate pending chat handling
                
                # Serialize MessageType enums to strings
                serialized_messages = []
                for msg in client_messages:
                    serialized_msg = msg.copy()
                    if 'type' in serialized_msg and hasattr(serialized_msg['type'], 'value'):
                        serialized_msg['type'] = serialized_msg['type'].value
                    serialized_messages.append(serialized_msg)
                
                action_data["client_message_batch"] = serialized_messages
                logger.info(f"CLIENT END_TURN DEBUG: Sending {len(client_messages)} messages in batch to host")
        
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
        """
        # Only host should process player actions
        if not self.network.is_host():
            return
        
        try:
            action_type = data.get("action_type", "")
            action_data = data.get("data", {})
            timestamp = data.get("timestamp", 0)
            
            # Queue the action to be applied
            self.pending_actions.append((action_type, action_data, timestamp))
            
            # Sort by timestamp
            self.pending_actions.sort(key=lambda x: x[2])
            
        except Exception as e:
            logger.error(f"Error handling player action: {str(e)}")
    
    def _apply_pending_actions(self) -> None:
        """
        Apply any pending player actions.
        """
        # Apply received game states (for non-host)
        if not self.network.is_host() and self.received_states:
            # Don't apply game state during setup phase - setup has its own message handling
            if not self.game.setup_phase:
                # Apply only the most recent state
                latest_state, _ = self.received_states[-1]
                self._deserialize_game_state(latest_state)
            self.received_states = []
        
        # Apply pending actions (for host)
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
            # Check if this is from a client and includes their message batch
            from boneglaive.utils.message_log import message_log
            
            # First check if client sent their message batch
            client_message_batch = data.get("client_message_batch", [])
            
            if client_message_batch:
                # Use client's message batch (they already collected their messages)
                turn_messages = client_message_batch
                logger.info(f"HOST END_TURN DEBUG: Using client's message batch with {len(turn_messages)} messages")
            else:
                # This is a host end_turn, collect host's messages
                try:
                    message_log.start_turn_batch()
                    
                    # Apply any planned actions from the ending player first
                    planned_actions = data.get("planned_actions", [])
                    if planned_actions:
                        self._apply_planned_actions(planned_actions)
                    
                    # Execute turn for all units with animations if UI available
                    if self.ui:
                        self.game.execute_turn(self.ui)
                    else:
                        self.game.execute_turn()
                    
                    # End message batching and collect messages
                    turn_messages = message_log.end_turn_batch()
                except Exception as batch_error:
                    logger.error(f"Error during message batching: {str(batch_error)}")
                    # Fallback: ensure batching is stopped and continue without messages
                    if message_log.is_batching:
                        message_log.end_turn_batch()
                    turn_messages = []
                
                # Chat messages are already included in turn_messages via batching
                # No need for separate pending chat handling
            
            # Apply any planned actions from the ending player if we haven't already
            if not client_message_batch:
                planned_actions = data.get("planned_actions", [])
                if planned_actions:
                    self._apply_planned_actions(planned_actions)
                
                # Execute turn for all units with animations if UI available
                if self.ui:
                    self.game.execute_turn(self.ui)
                else:
                    self.game.execute_turn()
            
            # Handle turn transition after execution (only host)
            if self.network.is_host():
                # Determine next player
                current_player = self.game.current_player
                next_player = 2 if current_player == 1 else 1
                
                logger.info(f"HOST END_TURN DEBUG: Before switch - current_player={current_player}, host_player_num={self.network.get_player_number()}")
                
                # Update game state
                if current_player == 1:
                    # Player 1 finished, switch to Player 2
                    self.game.current_player = 2
                elif current_player == 2:
                    # Player 2 finished, switch to Player 1 and increment turn
                    self.game.current_player = 1
                    self.game.turn += 1
                
                logger.info(f"HOST END_TURN DEBUG: After switch - new_current_player={self.game.current_player}, turn={self.game.turn}")
                
                # Initialize the new player's turn
                self.game.initialize_next_player_turn()
                
                # Send message batch to client first (if there are messages)
                if turn_messages:
                    # Serialize MessageType enums to strings for JSON transmission
                    serialized_messages = []
                    for msg in turn_messages:
                        serialized_msg = msg.copy()
                        if 'type' in serialized_msg and hasattr(serialized_msg['type'], 'value'):
                            serialized_msg['type'] = serialized_msg['type'].value
                        serialized_messages.append(serialized_msg)
                    
                    message_batch_msg = {
                        "messages": serialized_messages,
                        "from_player": current_player,
                        "turn_number": self.game.turn,
                        "timestamp": time.time()
                    }
                    success = self.network.send_message(MessageType.MESSAGE_LOG_BATCH, message_batch_msg)
                    if success:
                        logger.info(f"HOST END_TURN DEBUG: Sent MESSAGE_LOG_BATCH with {len(turn_messages)} messages from player {current_player}")
                    else:
                        logger.error(f"HOST END_TURN DEBUG: Failed to send MESSAGE_LOG_BATCH - connection may be lost")
                        return  # Don't proceed with turn transition if message batch failed
                
                # Small delay to ensure message batch is processed before turn transition
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
                
                # Update UI for host and handle message batching
                if self.ui:
                    from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                    if self.game.current_player == self.network.get_player_number():
                        # Host's turn again - start message batching
                        message_log.start_turn_batch()
                        message_log.add_system_message(f"Your turn - Turn {self.game.turn}")
                        self.ui.message = f"Your turn - Turn {self.game.turn}"
                        logger.info(f"HOST END_TURN DEBUG: Host UI updated - it's host's turn again, started message batching")
                    else:
                        # Client's turn - ensure batching is stopped
                        if message_log.is_batching:
                            message_log.end_turn_batch()  # Discard any partial batch
                        message_log.add_system_message(f"Player {self.game.current_player}'s turn - Turn {self.game.turn}")  
                        self.ui.message = f"Player {self.game.current_player} is thinking..."
                        logger.info(f"HOST END_TURN DEBUG: Host UI updated - it's client's turn now, stopped batching")
        
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
            
            # Add game start message and initialize batching
            if self.ui:
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                
                # Start message batching if I am Player 1
                if self.network.get_player_number() == 1:
                    message_log.start_turn_batch()
                    message_log.add_system_message(f"Game starting - Player 1's turn")
                    self.ui.message = f"Game starting - Player 1's turn"
                    logger.info("SETUP_COMPLETE DEBUG: Started message batching for Player 1's first turn")
                else:
                    message_log.add_system_message(f"Game starting - Player 1's turn")
                    self.ui.message = f"Player 1 is thinking..."
                    logger.info("SETUP_COMPLETE DEBUG: Player 2 waiting, no batching started")
                
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
            
            # Initialize the new player's turn locally
            self.game.initialize_next_player_turn()
            
            # Update UI and start/stop message batching based on turn
            if self.ui:
                from boneglaive.utils.message_log import message_log, MessageType as LogMessageType
                if new_player == self.network.get_player_number():
                    # It's my turn - start message batching
                    message_log.start_turn_batch()
                    message_log.add_system_message(f"Your turn - Turn {turn_number}")
                    self.ui.message = f"Your turn - Turn {turn_number}"
                    logger.info(f"TURN_TRANSITION DEBUG: UI updated - it's MY turn now, started message batching")
                else:
                    # Not my turn - ensure batching is stopped
                    if message_log.is_batching:
                        message_log.end_turn_batch()  # Discard any partial batch
                    message_log.add_system_message(f"Player {new_player}'s turn - Turn {turn_number}")
                    self.ui.message = f"Player {new_player} is thinking..."
                    logger.info(f"TURN_TRANSITION DEBUG: UI updated - it's OTHER player's turn, stopped batching")
                
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
        Handle received message log batch.
        Add the batch of messages to the local message log.
        """
        try:
            messages = data.get("messages", [])
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            
            logger.info(f"MESSAGE_LOG_BATCH DEBUG: Received batch with {len(messages)} messages from player {from_player} turn {turn_number}")
            
            if messages:
                from boneglaive.utils.message_log import message_log
                try:
                    message_log.add_batch_messages(messages)
                    logger.info(f"MESSAGE_LOG_BATCH DEBUG: Successfully added {len(messages)} messages to log")
                except Exception as add_error:
                    logger.error(f"Error adding messages to log: {str(add_error)}")
            else:
                logger.info(f"MESSAGE_LOG_BATCH DEBUG: No messages in batch to add")
            
        except Exception as e:
            logger.error(f"Error handling message log batch: {str(e)}")
        
        # Add more setup action types as needed