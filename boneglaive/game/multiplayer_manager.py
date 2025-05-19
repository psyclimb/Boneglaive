#!/usr/bin/env python3
"""
Manages multiplayer functionality for the game.
Handles different multiplayer modes and interfaces with the game engine.
"""

from typing import Optional, Tuple, Dict, Any

from boneglaive.game.engine import Game
from boneglaive.networking.network_interface import NetworkInterface
from boneglaive.networking.local_multiplayer import LocalMultiplayerInterface
from boneglaive.networking.lan_multiplayer import LANMultiplayerInterface
from boneglaive.ai.ai_interface import AIInterface
from boneglaive.utils.config import ConfigManager, NetworkMode
from boneglaive.utils.debug import logger
from boneglaive.utils.message_log import message_log, MessageType

class MultiplayerManager:
    """
    Manages multiplayer functionality, connecting the game engine
    with the appropriate network interface.
    """
    
    def __init__(self, game: Game):
        self.game = game
        self.config = ConfigManager()
        self.network_interface: Optional[NetworkInterface] = None
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
            self.initialized = result
            return result
            
        elif network_mode == NetworkMode.LAN_CLIENT.value:
            # LAN client uses LANMultiplayerInterface in client mode
            logger.info("Initializing LAN client")
            server_ip = self.config.get('server_ip')
            server_port = self.config.get('server_port')
            self.network_interface = LANMultiplayerInterface(host=False, server_ip=server_ip, port=server_port)
            result = self.network_interface.initialize()
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
            
        # For LAN multiplayer, check if the current player matches the network player number
        if self.is_network_multiplayer():
            return self.current_player == self.network_interface.get_player_number()
            
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

                # When switching to player 2, check if it's the first turn
                if is_switching_to_player2:
                    # If this is player 2's first turn, apply move bonus to all their units
                    if hasattr(self.game, 'is_player2_first_turn') and self.game.is_player2_first_turn:
                        self._apply_player2_first_turn_buff()
                        # Reset the flag for next time
                        self.game.is_player2_first_turn = False

                logger.info(f"Switched to player {self.current_player}")
        
        elif self.is_vs_ai():
            # In VS AI mode, switch between player 1 and AI (player 2)
            if self.current_player == 1:
                # Player 1 ended turn, switch to AI (player 2)
                self.current_player = 2
                self.game.current_player = 2
                
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
                    message_log.add_system_message("Player 1's turn")
                    
                    # Force UI refresh if UI is available
                    if ui and hasattr(ui, 'draw_board'):
                        ui.draw_board()
            else:
                # This shouldn't happen in VS AI mode, but handle it anyway
                self.current_player = 1
                self.game.current_player = 1

    def _apply_player2_first_turn_buff(self) -> None:
        """Apply +2 move range buff to all player 2 units on their first turn."""
        from boneglaive.utils.message_log import message_log, MessageType

        # Find all player 2 units and apply the buff
        player2_units = [unit for unit in self.game.units if unit.player == 2 and unit.is_alive()]

        if player2_units:
            # Apply the buff to each unit
            for unit in player2_units:
                # Add the move bonus (+1)
                unit.move_range_bonus += 1
                # Add a flag to show the status effect icon
                unit.first_turn_move_bonus = True

            # Show a message about the buff
            message_log.add_message(
                "Player 2 units gain +1 movement range on their first turn!",
                MessageType.SYSTEM
            )
    
    def get_current_player(self) -> int:
        """Get the current player number (1 or 2)."""
        if not self.is_multiplayer():
            return 1
        
        if self.is_local_multiplayer():
            if isinstance(self.network_interface, LocalMultiplayerInterface):
                return self.network_interface.get_player_number()
        
        return self.current_player
    
    def cleanup(self) -> None:
        """Clean up network resources."""
        if self.network_interface:
            self.network_interface.cleanup()
            self.network_interface = None
        self.initialized = False
        logger.info("Multiplayer manager cleaned up")