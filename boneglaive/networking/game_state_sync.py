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
    
    def __init__(self, game: Game, network: NetworkInterface):
        self.game = game
        self.network = network
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
            unit = self.game.add_unit(unit_type, player, y, x)
            
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
        # Only non-host players need to send actions
        if self.network.is_host():
            # Host can apply actions directly
            self._apply_action(action_type, data)
            return
        
        # Send action to host
        self.network.send_message(MessageType.PLAYER_ACTION, {
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
                    break
        
        elif action_type == "attack":
            unit_id = data.get("unit_id")
            target = data.get("target")
            
            # Find unit by ID
            for unit in self.game.units:
                if id(unit) == unit_id and unit.is_alive():
                    unit.attack_target = target
                    break
        
        elif action_type == "end_turn":
            # Execute turn for all units
            self.game.execute_turn()
        
        # Add more action types as needed