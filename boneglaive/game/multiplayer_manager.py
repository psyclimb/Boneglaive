#!/usr/bin/env python3
"""
Manages multiplayer functionality for the game.
Handles different multiplayer modes and interfaces with the game engine.
"""

import time
from typing import Optional, Tuple, Dict, Any

from boneglaive.game.engine import Game
from boneglaive.networking.network_interface import NetworkInterface
from boneglaive.networking.local_multiplayer import LocalMultiplayerInterface
from boneglaive.networking.lan_multiplayer import LANMultiplayerInterface
from boneglaive.networking.game_state_sync import GameStateSync
from boneglaive.ai.ai_interface import AIInterface
from boneglaive.utils.config import ConfigManager, NetworkMode
from boneglaive.utils.debug import logger
from boneglaive.utils.message_log import message_log, MessageType as LogMessageType

class MultiplayerManager:
    """
    Manages multiplayer functionality, connecting the game engine
    with the appropriate network interface.
    """
    
    def __init__(self, game: Game):
        self.game = game
        self.config = ConfigManager()
        self.network_interface: Optional[NetworkInterface] = None
        self.game_state_sync: Optional[GameStateSync] = None
        self.initialized = False
        self.current_player = 1
        
        # Initialize appropriate network interface based on config
        self._initialize_network()
    
    def _initialize_network(self) -> bool:
        """Initialize the appropriate network interface."""
        network_mode = self.config.get('network_mode')
        
        if network_mode == NetworkMode.SINGLE_PLAYER.value:
            # Single player doesn't need a network interface
            logger.info("Initializing single player mode")
            self.game.local_multiplayer = False
            self.initialized = True
            return True
            
        elif network_mode == NetworkMode.LOCAL_MULTIPLAYER.value:
            # Local multiplayer uses the LocalMultiplayerInterface
            logger.info("Initializing local multiplayer")
            self.network_interface = LocalMultiplayerInterface()
            result = self.network_interface.initialize()
            self.initialized = result
            
            # Mark the game as being in local multiplayer mode
            if result:
                self.game.local_multiplayer = True
                logger.info("Local multiplayer initialized successfully")
            
            return result
            
        elif network_mode == NetworkMode.LAN_HOST.value:
            # LAN host uses LANMultiplayerInterface in host mode
            logger.info("Initializing LAN host")
            server_port = self.config.get('server_port')
            self.network_interface = LANMultiplayerInterface(host=True, port=server_port)
            result = self.network_interface.initialize()
            if result:
                pass  # Chat is now handled via turn batching
                # Set current player based on network role (this is your network identity, not turn player)
                self.current_player = self.network_interface.get_player_number()
                # Game always starts with Player 1's turn, regardless of which network player you are
                self.game.current_player = 1
                # For LAN multiplayer, turn switching is handled by network layer, not game engine
                # Set local_multiplayer = True to prevent game engine from doing its own turn switching
                self.game.local_multiplayer = True
                # Initialize game state synchronization
                self.game_state_sync = GameStateSync(self.game, self.network_interface, self)
                logger.info(f"MULTIPLAYER INIT DEBUG: LAN host initialized as player {self.current_player}, game.current_player={self.game.current_player}, local_multiplayer={self.game.local_multiplayer} with game state sync")
            self.initialized = result
            return result
            
        elif network_mode == NetworkMode.LAN_CLIENT.value:
            # LAN client uses LANMultiplayerInterface in client mode
            logger.info("Initializing LAN client")
            server_ip = self.config.get('server_ip')
            server_port = self.config.get('server_port')
            self.network_interface = LANMultiplayerInterface(host=False, server_ip=server_ip, port=server_port)
            result = self.network_interface.initialize()
            if result:
                pass  # Chat is now handled via turn batching
                # Set current player based on network role (this is your network identity, not turn player)
                self.current_player = self.network_interface.get_player_number()
                # Game always starts with Player 1's turn, regardless of which network player you are
                self.game.current_player = 1
                # For LAN multiplayer, turn switching is handled by network layer, not game engine
                # Set local_multiplayer = True to prevent game engine from doing its own turn switching
                self.game.local_multiplayer = True
                # Initialize game state synchronization
                self.game_state_sync = GameStateSync(self.game, self.network_interface, self)
                logger.info(f"MULTIPLAYER INIT DEBUG: LAN client initialized as player {self.current_player}, game.current_player={self.game.current_player}, local_multiplayer={self.game.local_multiplayer} with game state sync")
            self.initialized = result
            return result
            
        elif network_mode == NetworkMode.VS_AI.value:
            # VS AI mode using AIInterface
            logger.info("Initializing VS AI mode")
            self.network_interface = AIInterface()
            result = self.network_interface.initialize(self.game, ui=getattr(self.game, 'ui', None))
            self.initialized = result
            
            # Mark the game as being in single player mode (not local multiplayer)
            if result:
                self.game.local_multiplayer = False
                logger.info("VS AI mode initialized successfully")
            else:
                logger.error("Failed to initialize VS AI mode")
            
            return result
            
        else:
            logger.error(f"Unknown network mode: {network_mode}")
            self.initialized = False
            return False
    
    
    def is_current_player_turn(self) -> bool:
        """Check if it's the current player's turn."""
        if not self.is_multiplayer():
            # In single player, it's always the player's turn
            return True
            
        # For LAN multiplayer, check if the game's current turn player matches your network player number  
        if self.is_network_multiplayer():
            result = self.game.current_player == self.network_interface.get_player_number()
            logger.debug(f"TURN_CHECK DEBUG: game.current_player={self.game.current_player}, my_player_num={self.network_interface.get_player_number()}, is_my_turn={result}")
            return result
            
        # For local multiplayer, always return true since both players are on the same computer
        # and take turns physically passing control
        return True
    
    def is_multiplayer(self) -> bool:
        """Check if the game is in multiplayer mode."""
        return self.network_interface is not None and self.network_interface.is_multiplayer()
    
    def is_local_multiplayer(self) -> bool:
        """Check if the game is in local multiplayer mode."""
        return (self.network_interface is not None and 
                self.network_interface.is_local_multiplayer())
    
    def is_network_multiplayer(self) -> bool:
        """Check if the game is in network multiplayer mode (LAN)."""
        return (self.network_interface is not None and 
                self.network_interface.is_network_multiplayer())
    
    def is_vs_ai(self) -> bool:
        """Check if the game is in vs. AI mode."""
        return isinstance(self.network_interface, AIInterface)
    
    def end_turn(self) -> None:
        """End the current player's turn and switch to the next player."""
        if not self.is_multiplayer() and not self.is_vs_ai():
            # In single player (not vs. AI), no need to switch players
            return

        if self.is_local_multiplayer():
            # In local multiplayer, switch players
            if isinstance(self.network_interface, LocalMultiplayerInterface):
                # Check if we're switching to player 2
                is_switching_to_player2 = self.current_player == 1

                # Update current player
                self.network_interface.switch_player()
                self.current_player = self.network_interface.get_player_number()

                # Ensure the player number in the game engine is also updated
                self.game.current_player = self.current_player
                
                # Increment turn counter when switching back to player 1
                if self.current_player == 1:
                    self.game.turn += 1

                # Initialize the new player's turn (apply passive skills and reset flags)
                self.game.initialize_next_player_turn()

                # When switching to player 2, check if it's the first turn
                if is_switching_to_player2:
                    # If this is player 2's first turn, apply move bonus to all their units
                    if hasattr(self.game, 'is_player2_first_turn') and self.game.is_player2_first_turn:
                        self._apply_player2_first_turn_buff()
                        # Reset the flag for next time
                        self.game.is_player2_first_turn = False

                logger.info(f"Switched to player {self.current_player}")
        
        elif self.is_network_multiplayer():
            # In network multiplayer, turn switching is handled by the host
            # through GameStateSync - the current player doesn't change locally
            # until we receive a turn transition message from the host
            logger.info(f"Network multiplayer turn end - current player stays {self.current_player}")
            # Turn switching will be handled by GameStateSync when turn execution completes
            
        elif self.is_vs_ai():
            # In VS AI mode, switch between player 1 and AI (player 2)
            if self.current_player == 1:
                # Player 1 ended turn, switch to AI (player 2)
                self.current_player = 2
                self.game.current_player = 2
                
                # Initialize the AI player's turn
                self.game.initialize_next_player_turn()
                
                # If this is player 2's first turn, apply move bonus to their units
                if hasattr(self.game, 'is_player2_first_turn') and self.game.is_player2_first_turn:
                    self._apply_player2_first_turn_buff()
                    self.game.is_player2_first_turn = False
                
                # Process AI turn immediately
                logger.info("Processing AI turn")
                if isinstance(self.network_interface, AIInterface):
                    # Get UI reference from game if available
                    ui = getattr(self.game, 'ui', None)
                    
                    # Process AI turn
                    message_log.add_system_message("AI is thinking...")
                    self.network_interface.process_turn()
                    
                    # Execute the AI's turn
                    logger.info("Executing AI's turn")
                    self.game.execute_turn(ui)
                    
                    # Switch back to player 1 after AI turn
                    self.current_player = 1
                    self.game.current_player = 1
                    
                    # Increment turn counter when switching back to player 1
                    self.game.turn += 1
                    
                    # Initialize player 1's turn
                    self.game.initialize_next_player_turn()
                    
                    message_log.add_system_message("Player 1's turn")
                    
                    # Force UI refresh if UI is available
                    if ui and hasattr(ui, 'draw_board'):
                        ui.draw_board()
            else:
                # This shouldn't happen in VS AI mode, but handle it anyway
                self.current_player = 1
                self.game.current_player = 1
                self.game.initialize_next_player_turn()

    def _apply_player2_first_turn_buff(self) -> None:
        """Apply +2 move range buff to all player 2 units on their first turn."""
        from boneglaive.utils.message_log import message_log, MessageType

        # Find all player 2 units and apply the buff
        player2_units = [unit for unit in self.game.units if unit.player == 2 and unit.is_alive()]

        if player2_units:
            # Apply the buff to each unit
            for unit in player2_units:
                # Check if unit is immune to status effects (GRAYMAN with Stasiality)
                if unit.is_immune_to_effects():
                    logger.debug(f"{unit.get_display_name()} is immune to first turn bonus due to Stasiality")
                    continue
                
                # Add the move bonus (+1)
                unit.move_range_bonus += 1
                # Add a flag to show the status effect icon
                unit.first_turn_move_bonus = True

            # Show a message about the buff
            message_log.add_message(
                "Player 2 units gain +1 movement range on their first turn",
                MessageType.SYSTEM
            )
    
    def get_current_player(self) -> int:
        """Get the current player number (1 or 2)."""
        if not self.is_multiplayer():
            return 1
        
        if self.is_local_multiplayer():
            if isinstance(self.network_interface, LocalMultiplayerInterface):
                return self.network_interface.get_player_number()
        
        # For network multiplayer (LAN), return the game engine's current player
        # This is synchronized through GameStateSync turn transitions
        if self.is_network_multiplayer():
            return self.game.current_player
        
        return self.current_player
    
    def send_player_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """Send a player action through the network (if networked) or apply directly."""
        if self.game_state_sync and self.is_network_multiplayer():
            # Route through GameStateSync for networked games
            self.game_state_sync.send_player_action(action_type, data)
            logger.debug(f"Sent network action: {action_type}")
        else:
            # For local games, apply actions directly to game engine
            logger.debug(f"Applied local action: {action_type}")
            # TODO: Apply action directly to game state for non-networked games
    
    def set_ui_reference(self, ui) -> None:
        """Set UI reference for game state sync animations."""
        if self.game_state_sync:
            self.game_state_sync.set_ui_reference(ui)
    
    def update(self) -> None:
        """Update multiplayer state - call this each game loop iteration."""
        if self.network_interface and self.is_network_multiplayer():
            # Check connection status
            if hasattr(self.network_interface, 'connected') and not self.network_interface.connected:
                if self.initialized:  # Only report once
                    message_log.add_system_message("Network connection lost")
                    self.initialized = False
            
            # Update game state synchronization
            if self.game_state_sync:
                self.game_state_sync.update()
            else:
                # Fallback to basic message processing if GameStateSync not available
                self.network_interface.receive_messages()
    
    def cleanup(self) -> None:
        """Clean up network resources."""
        if self.network_interface:
            self.network_interface.cleanup()
            self.network_interface = None
        if self.game_state_sync:
            self.game_state_sync = None
        self.initialized = False
        logger.info("Multiplayer manager cleaned up")