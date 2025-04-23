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
            # VS AI mode uses AIInterface
            logger.info("Initializing vs AI mode")
            ai_difficulty = self.config.get('ai_difficulty')
            self.network_interface = AIInterface(difficulty=ai_difficulty)
            
            # Initialize the AI interface
            result = self.network_interface.initialize()
            self.initialized = result
            
            # Set the game reference so the AI can interact with it
            if result:
                # Make sure we give the AI interface a reference to the game
                self.network_interface.set_game(self.game)
                # Mark the game as being in local multiplayer mode (for turn handling)
                self.game.local_multiplayer = True
                logger.info(f"AI interface initialized with difficulty: {ai_difficulty}")
                # Log current player state for debugging
                logger.debug(f"Current player in game: {self.game.current_player}")
                logger.debug(f"AI player: {self.network_interface.ai_player_number}")
                logger.debug(f"Human player: {self.network_interface.human_player_number}")
                
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
    
    def end_turn(self) -> None:
        """End the current player's turn and switch to the next player."""
        if not self.is_multiplayer():
            # In single player, no need to switch players
            return
            
        if self.is_local_multiplayer():
            # In local multiplayer, switch players
            if isinstance(self.network_interface, LocalMultiplayerInterface):
                self.network_interface.switch_player()
                self.current_player = self.network_interface.get_player_number()
                # Ensure the player number in the game engine is also updated
                # This is redundant with our engine.py change but ensures consistency
                self.game.current_player = self.current_player
                logger.info(f"Switched to player {self.current_player}")
    
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