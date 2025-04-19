#!/usr/bin/env python3
"""
Game server for LAN multiplayer mode.
Can be run as a standalone server or embedded in a game client.
"""

import json
import socket
import threading
import time
from typing import Dict, List, Optional, Set, Tuple, Union

from boneglaive.networking.network_interface import MessageType
from boneglaive.utils.debug import logger

# Server configuration
DEFAULT_PORT = 7777
MAX_CLIENTS = 10
BUFFER_SIZE = 4096
MESSAGE_DELIMITER = b"\n"

class GameServer:
    """
    Game server for managing LAN multiplayer connections.
    Can be run as a standalone server for hosting multiple games.
    """
    
    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # client_id -> socket
        self.client_addresses = {}  # client_id -> address
        self.games = {}  # game_id -> [client_id1, client_id2]
        self.threads = []
        self.accept_thread = None
    
    def start(self) -> bool:
        """Start the server."""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(MAX_CLIENTS)
            
            self.running = True
            logger.info(f"Game server started on port {self.port}")
            
            # Start accept thread
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
            return False
    
    def stop(self) -> None:
        """Stop the server."""
        self.running = False
        
        # Close client connections
        for client_id, client_socket in list(self.clients.items()):
            try:
                client_socket.close()
            except:
                pass
        self.clients.clear()
        self.client_addresses.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Wait for threads to terminate
        for thread in self.threads:
            if thread.is_alive():
                thread.join(1.0)
        self.threads.clear()
        
        if self.accept_thread and self.accept_thread.is_alive():
            self.accept_thread.join(1.0)
        
        logger.info("Game server stopped")
    
    def _accept_connections(self) -> None:
        """Thread for accepting client connections."""
        while self.running and self.server_socket:
            try:
                client_socket, addr = self.server_socket.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                
                logger.info(f"Client connected: {client_id}")
                
                # Store client information
                self.clients[client_id] = client_socket
                self.client_addresses[client_id] = addr
                
                # Start client thread
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_id, client_socket)
                )
                client_thread.daemon = True
                client_thread.start()
                self.threads.append(client_thread)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {str(e)}")
    
    def _handle_client(self, client_id: str, client_socket: socket.socket) -> None:
        """Handle communication with a client."""
        buffer = b""
        
        while self.running and client_id in self.clients:
            try:
                # Receive data
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    # Connection closed
                    break
                
                # Add to buffer and process complete messages
                buffer += data
                messages = buffer.split(MESSAGE_DELIMITER)
                
                # Process all complete messages
                for i in range(len(messages) - 1):
                    try:
                        message = json.loads(messages[i].decode('utf-8'))
                        self._process_message(client_id, message)
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from {client_id}: {messages[i]}")
                
                # Keep the incomplete message in the buffer
                buffer = messages[-1]
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error handling client {client_id}: {str(e)}")
                break
        
        # Client disconnected, clean up
        self._disconnect_client(client_id)
    
    def _disconnect_client(self, client_id: str) -> None:
        """Handle client disconnection."""
        if client_id in self.clients:
            try:
                self.clients[client_id].close()
            except:
                pass
            
            del self.clients[client_id]
            
            if client_id in self.client_addresses:
                del self.client_addresses[client_id]
            
            # Notify game partner if in a game
            for game_id, players in list(self.games.items()):
                if client_id in players:
                    for player_id in players:
                        if player_id != client_id and player_id in self.clients:
                            self._send_message(player_id, MessageType.DISCONNECT, {
                                "reason": "Partner disconnected"
                            })
                    del self.games[game_id]
            
            logger.info(f"Client disconnected: {client_id}")
    
    def _process_message(self, client_id: str, message: Dict) -> None:
        """Process a message from a client."""
        try:
            message_type = MessageType(message.get('type'))
            data = message.get('data', {})
            target = data.get('target', None)
            
            # Handle message based on type
            if message_type == MessageType.CONNECT:
                # Client is connecting, might need to create or join a game
                game_id = data.get('game_id')
                if game_id and game_id in self.games:
                    # Join existing game
                    if len(self.games[game_id]) < 2:
                        self.games[game_id].append(client_id)
                        
                        # Notify both players
                        for player_id in self.games[game_id]:
                            self._send_message(player_id, MessageType.CONNECT, {
                                "game_id": game_id,
                                "players": self.games[game_id]
                            })
                else:
                    # Create new game
                    new_game_id = data.get('game_id', f"game-{int(time.time())}")
                    self.games[new_game_id] = [client_id]
                    
                    # Notify client
                    self._send_message(client_id, MessageType.CONNECT, {
                        "game_id": new_game_id,
                        "players": self.games[new_game_id]
                    })
            
            elif target:
                # Forward message to target
                if target in self.clients:
                    self._send_raw_message(target, message)
                else:
                    # Target not found, send error to sender
                    self._send_message(client_id, MessageType.ERROR, {
                        "error": "Target not found",
                        "target": target
                    })
        
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid message from {client_id}: {str(e)}")
            self._send_message(client_id, MessageType.ERROR, {
                "error": f"Invalid message: {str(e)}"
            })
    
    def _send_message(self, client_id: str, message_type: MessageType, 
                     data: Dict) -> bool:
        """Send a message to a client."""
        if client_id not in self.clients:
            return False
        
        try:
            message = {
                'type': message_type.value,
                'data': data,
                'sender': 'server',
                'timestamp': time.time()
            }
            
            # Encode and send the message
            message_bytes = json.dumps(message).encode('utf-8') + MESSAGE_DELIMITER
            self.clients[client_id].sendall(message_bytes)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {str(e)}")
            self._disconnect_client(client_id)
            return False
    
    def _send_raw_message(self, client_id: str, message: Dict) -> bool:
        """Send a raw message to a client."""
        if client_id not in self.clients:
            return False
        
        try:
            # Ensure timestamp is present
            if 'timestamp' not in message:
                message['timestamp'] = time.time()
            
            # Encode and send the message
            message_bytes = json.dumps(message).encode('utf-8') + MESSAGE_DELIMITER
            self.clients[client_id].sendall(message_bytes)
            return True
        except Exception as e:
            logger.error(f"Error sending raw message to {client_id}: {str(e)}")
            self._disconnect_client(client_id)
            return False
    
    def broadcast(self, message_type: MessageType, data: Dict) -> None:
        """Send a message to all connected clients."""
        for client_id in list(self.clients.keys()):
            self._send_message(client_id, message_type, data)
    
    def get_stats(self) -> Dict:
        """Get server statistics."""
        return {
            "running": self.running,
            "clients_count": len(self.clients),
            "games_count": len(self.games),
            "port": self.port
        }
    
    def get_games(self) -> Dict:
        """Get information about active games."""
        games_info = {}
        for game_id, players in self.games.items():
            games_info[game_id] = {
                "players": players,
                "player_count": len(players),
                "joinable": len(players) < 2
            }
        return games_info