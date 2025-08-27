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
        
        # For client end_turn, collect and send turn messages to host first
        if action_type == "end_turn":
            from boneglaive.utils.message_log import message_log
            
            # Collect turn messages from client
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
                game_state = game_state_serializer.serialize_game_state(self.game)
                state_checksum = game_state_serializer.generate_checksum(self.game)
                
                game_state_msg = {
                    "state": game_state,
                    "from_player": current_game_player,
                    "turn_number": self.game.turn,
                    "checksum": state_checksum,
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
                    "from_player": current_player,
                    "turn_number": self.game.turn,
                    "checksum": state_checksum,
                    "timestamp": time.time()
                }
                
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
            
            logger.info(f"MESSAGE_LOG_BATCH DEBUG: Received {len(messages)} messages from player {from_player} turn {turn_number}")
            
            if messages:
                from boneglaive.utils.message_log import message_log
                message_log.add_network_messages(messages)
                logger.info(f"MESSAGE_LOG_BATCH DEBUG: Added {len(messages)} network messages to log")
                
                # Perform parity check if checksum was provided
                if other_checksum:
                    parity_match = message_log.verify_parity(other_checksum, from_player)
                    
                    # Send our checksum back for verification
                    my_checksum = message_log.get_message_log_checksum()
                    parity_response = {
                        "checksum": my_checksum,
                        "from_player": self.network.get_player_number(),
                        "parity_match": parity_match,
                        "turn_number": turn_number,
                        "timestamp": time.time()
                    }
                    
                    self.network.send_message(MessageType.PARITY_CHECK, parity_response)
                    logger.info(f"PARITY_CHECK DEBUG: Sent checksum response {my_checksum} (match: {parity_match})")
                    
                    # If there's a mismatch, request full sync from the other player
                    if not parity_match:
                        logger.warning(f"SYNC RECOVERY: Requesting full message log from Player {from_player}")
                        sync_request = {
                            "from_player": self.network.get_player_number(),
                            "turn_number": turn_number,
                            "timestamp": time.time()
                        }
                        self.network.send_message(MessageType.MESSAGE_LOG_SYNC_REQUEST, sync_request)
            
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
            
            logger.info(f"PARITY_CHECK DEBUG: Received checksum {other_checksum} from player {from_player} (match: {parity_match})")
            
            if other_checksum:
                from boneglaive.utils.message_log import message_log
                
                # Verify parity from our side as well
                my_parity_match = message_log.verify_parity(other_checksum, from_player)
                
                # Log the final parity result
                if parity_match and my_parity_match:
                    logger.info(f"PARITY_CHECK RESULT: ✓ Message logs are in perfect sync after turn {turn_number}")
                else:
                    logger.warning(f"PARITY_CHECK RESULT: ✗ Message log sync issue detected after turn {turn_number}")
                    logger.warning(f"Their verification: {parity_match}, My verification: {my_parity_match}")
                    
                    # Request full sync from other player to fix the issue
                    logger.warning(f"SYNC RECOVERY: Requesting full message log from Player {from_player}")
                    sync_request = {
                        "from_player": self.network.get_player_number(),
                        "turn_number": turn_number,
                        "timestamp": time.time()
                    }
                    self.network.send_message(MessageType.MESSAGE_LOG_SYNC_REQUEST, sync_request)
            
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
        Verify parity and trigger recovery if needed.
        """
        try:
            state_data = data.get("state", {})
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            other_checksum = data.get("checksum", "")
            
            logger.info(f"GAME_STATE_BATCH DEBUG: Received game state from player {from_player} turn {turn_number}")
            
            if state_data and other_checksum:
                # Generate our current game state checksum
                my_checksum = game_state_serializer.generate_checksum(self.game)
                
                # Compare checksums for parity check
                parity_match = my_checksum == other_checksum
                
                logger.info(f"GAME_STATE_PARITY DEBUG: My checksum={my_checksum}, Their checksum={other_checksum}, Match={parity_match}")
                
                # Send parity check response
                parity_response = {
                    "my_checksum": my_checksum,
                    "their_checksum": other_checksum,
                    "from_player": self.network.get_player_number(),
                    "parity_match": parity_match,
                    "turn_number": turn_number,
                    "timestamp": time.time()
                }
                
                self.network.send_message(MessageType.GAME_STATE_PARITY_CHECK, parity_response)
                logger.info(f"GAME_STATE_PARITY DEBUG: Sent parity response (match: {parity_match})")
                
                # If there's a mismatch, use structured recovery system
                if not parity_match:
                    logger.warning(f"GAME_STATE_RECOVERY: Game state desync detected - using structured recovery")
                    self.handle_state_desync(other_checksum, from_player, turn_number)
                
        except Exception as e:
            logger.error(f"Error handling game state batch: {str(e)}")
    
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
        Replace our game state with theirs to fix sync issues.
        """
        try:
            state_data = data.get("state", {})
            other_checksum = data.get("checksum", "")
            from_player = data.get("from_player", 0)
            turn_number = data.get("turn_number", 0)
            
            logger.warning(f"GAME_STATE_FULL_SYNC DEBUG: Received full game state from Player {from_player}")
            
            if state_data and other_checksum:
                # Use structured recovery system with UI preservation
                recovery_success = self.replace_game_state_with_recovery(
                    state_data, other_checksum, from_player
                )
                
                if not recovery_success:
                    logger.error(f"GAME_STATE_RECOVERY: ✗ Structured recovery failed for Player {from_player}")
                    # Could implement additional fallback mechanisms here if needed
            
        except Exception as e:
            logger.error(f"Error handling game state full sync: {str(e)}")
    
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
        Phase 5.4: Turn-end sync integration pattern.
        
        This method should be called after all turn effects are resolved
        but before transitioning to the next player's turn.
        """
        try:
            current_turn = self.game.turn
            current_player = self.game.current_player
            
            logger.info(f"END_OF_TURN_SYNC: Starting turn {current_turn} player {current_player} sync")
            
            # Send complete game state to other player
            batch_sent = self.send_game_state_batch(current_turn)
            
            if not batch_sent:
                logger.warning(f"END_OF_TURN_SYNC: Game state batch failed - sync incomplete")
                return False
            
            logger.info(f"END_OF_TURN_SYNC: ✓ Turn {current_turn} sync completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in end-of-turn sync: {str(e)}")
            return False
    
    # ===== PHASE 5.5: RECOVERY & ERROR HANDLING METHODS =====
    
    def handle_state_desync(self, other_checksum: str, from_player: int, turn_number: int) -> bool:
        """
        Handle detected game state desync by requesting authoritative state.
        Phase 5.5: Comprehensive desync detection and recovery.
        """
        try:
            my_checksum = game_state_serializer.generate_checksum(self.game)
            
            logger.warning(f"DESYNC_HANDLER: Game state desync detected!")
            logger.warning(f"  Turn: {turn_number}, From Player: {from_player}")
            logger.warning(f"  My checksum: {my_checksum}")
            logger.warning(f"  Their checksum: {other_checksum}")
            
            # Request full game state from the other player
            return self.request_full_game_state_sync(from_player, turn_number)
            
        except Exception as e:
            logger.error(f"Error handling state desync: {str(e)}")
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
                                       expected_checksum: str, from_player: int) -> bool:
        """
        Replace entire game state with authoritative version, preserving UI state.
        Phase 5.5: Complete state recovery with UI preservation.
        """
        try:
            logger.warning(f"STATE_REPLACEMENT: Starting full game state recovery from Player {from_player}")
            
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