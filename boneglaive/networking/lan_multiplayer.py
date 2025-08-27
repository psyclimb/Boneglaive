#!/usr/bin/env python3
"""
Implementation of LAN multiplayer mode using socket-based networking.
"""

import json
import socket
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from boneglaive.networking.network_interface import GameMode, MessageType, NetworkInterface
from boneglaive.utils.debug import debug_config, logger

# Default network settings
DEFAULT_PORT = 7777
BUFFER_SIZE = 4096
CONNECT_TIMEOUT = 10.0
MESSAGE_DELIMITER = b"\n"

class LANMultiplayerInterface(NetworkInterface):
    """Implementation for LAN multiplayer."""
    
    def __init__(self, host: bool = False, server_ip: Optional[str] = None, 
                port: int = DEFAULT_PORT):
        super().__init__(GameMode.NETWORK_MULTIPLAYER)
        self.is_server = host
        self.server_ip = server_ip if not host else None
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.connected = False
        self.receive_thread = None
        self.stop_thread = False
        self.message_queue = []
    
    def initialize(self) -> bool:
        """Initialize the network connection."""
        try:
            if self.is_server:
                return self._initialize_server()
            else:
                return self._initialize_client()
        except Exception as e:
            logger.error(f"Network initialization error: {str(e)}")
            return False
    
    def _initialize_server(self) -> bool:
        """Initialize as server (host)."""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port))
            self.server_socket.settimeout(CONNECT_TIMEOUT)
            self.server_socket.listen(1)
            
            logger.info(f"Server started, waiting for connections on port {self.port}")
            
            # Wait for client to connect
            self.client_socket, addr = self.server_socket.accept()
            self.opponent_id = f"{addr[0]}:{addr[1]}"
            logger.info(f"Client connected from {self.opponent_id}")
            
            # Start receive thread
            self._start_receive_thread()
            
            # Send connection confirmation
            self.send_message(MessageType.CONNECT, {
                "player_id": self.player_id,
                "player_number": 1
            })
            
            self.connected = True
            return True
            
        except socket.timeout:
            logger.error("Connection timeout waiting for client")
            if self.server_socket:
                self.server_socket.close()
            return False
        except Exception as e:
            logger.error(f"Server initialization error: {str(e)}")
            if self.server_socket:
                self.server_socket.close()
            return False
    
    def _initialize_client(self) -> bool:
        """Initialize as client."""
        try:
            # Check if server IP is provided
            if not self.server_ip:
                logger.error("Server IP address not provided")
                return False
            
            # Create client socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(CONNECT_TIMEOUT)
            
            # Connect to server
            logger.info(f"Connecting to server at {self.server_ip}:{self.port}")
            self.client_socket.connect((self.server_ip, self.port))
            self.opponent_id = f"{self.server_ip}:{self.port}"
            
            # Start receive thread
            self._start_receive_thread()
            
            # Send connection confirmation
            self.send_message(MessageType.CONNECT, {
                "player_id": self.player_id,
                "player_number": 2
            })
            
            self.connected = True
            return True
            
        except socket.timeout:
            logger.error(f"Connection timeout connecting to {self.server_ip}:{self.port}")
            if self.client_socket:
                self.client_socket.close()
            return False
        except Exception as e:
            logger.error(f"Client initialization error: {str(e)}")
            if self.client_socket:
                self.client_socket.close()
            return False
    
    def _start_receive_thread(self) -> None:
        """Start the message receiving thread."""
        self.stop_thread = False
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
    
    def _receive_loop(self) -> None:
        """Background thread for receiving messages."""
        buffer = b""
        
        while not self.stop_thread and self.client_socket:
            try:
                # Receive data
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    # Connection closed
                    logger.info("Connection closed by peer")
                    self.connected = False
                    break
                
                # Add to buffer and process complete messages
                buffer += data
                messages = buffer.split(MESSAGE_DELIMITER)
                
                # Process all complete messages
                for i in range(len(messages) - 1):
                    try:
                        message = json.loads(messages[i].decode('utf-8'))
                        # Validate message structure
                        if isinstance(message, dict) and 'type' in message and 'data' in message:
                            logger.info(f"NETWORK RECEIVE DEBUG: Received {message['type']} message: {message['data']}")
                            self.message_queue.append(message)
                        else:
                            logger.warning(f"Received message with invalid structure: {message}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Received invalid JSON: {messages[i]}, error: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                
                # Keep the incomplete message in the buffer
                buffer = messages[-1]
                
            except socket.timeout:
                # Just a timeout, continue
                continue
            except Exception as e:
                logger.error(f"Error in receive loop: {str(e)}")
                self.connected = False
                break
    
    def receive_messages(self) -> None:
        """Process any queued messages."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            try:
                message_type = MessageType(message.get('type'))
                data = message.get('data', {})
                self._handle_message(message_type, data)
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid message format: {str(e)}")
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """Send a message to the other player."""
        if not self.connected or not self.client_socket:
            return False
        
        try:
            message = {
                'type': message_type.value,
                'data': data,
                'sender': self.player_id,
                'timestamp': time.time()
            }
            
            # Log message being sent for debugging
            logger.info(f"NETWORK SEND DEBUG: Sending {message_type.value} message: {data}")
            
            # Encode and send the message
            try:
                message_json = json.dumps(message)
                message_bytes = message_json.encode('utf-8') + MESSAGE_DELIMITER
                self.client_socket.sendall(message_bytes)
                return True
            except (TypeError, ValueError) as json_err:
                logger.error(f"JSON serialization error for {message_type.value}: {str(json_err)}")
                logger.error(f"Problem message data: {data}")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.connected = False
            return False
    
    def cleanup(self) -> None:
        """Clean up network resources."""
        # Stop the receive thread
        self.stop_thread = True
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(1.0)
        
        # Close sockets
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        self.connected = False
        logger.info("Network connection cleaned up")
    
    def is_host(self) -> bool:
        """Check if this client is the host/server."""
        return self.is_server
    
    def get_player_number(self) -> int:
        """Get the player number (1 for host, 2 for client)."""
        return 1 if self.is_server else 2