#!/usr/bin/env python3
"""
Test script for LAN chat functionality.
This helps verify that bidirectional messaging works between host and client.
"""

import sys
import os

# Add the boneglaive directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boneglaive'))

from boneglaive.networking.lan_multiplayer import LANMultiplayerInterface
from boneglaive.networking.network_interface import MessageType
from boneglaive.utils.message_log import message_log
import time
import threading

def test_host():
    """Test as LAN host."""
    print("=== Testing as LAN Host ===")
    
    # Create host interface
    host = LANMultiplayerInterface(host=True, port=7777)
    
    # Set up chat message handler
    def handle_chat(data):
        player = data.get('player')
        message = data.get('message')
        print(f"HOST received: [Player {player}] {message}")
        message_log.add_player_message(player, message)
    
    host.register_message_handler(MessageType.CHAT, handle_chat)
    
    # Initialize connection
    print("HOST: Starting server on port 7777...")
    if host.initialize():
        print("HOST: Client connected!")
        
        # Send a test message
        time.sleep(1)
        print("HOST: Sending test message...")
        success = host.send_message(MessageType.CHAT, {
            "player": 1,
            "message": "Hello from host!"
        })
        print(f"HOST: Message send {'successful' if success else 'failed'}")
        
        # Process messages for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            host.receive_messages()
            time.sleep(0.1)
            
    else:
        print("HOST: Failed to initialize!")
    
    host.cleanup()
    print("HOST: Cleanup complete")

def test_client(server_ip="127.0.0.1"):
    """Test as LAN client."""
    print(f"=== Testing as LAN Client (connecting to {server_ip}) ===")
    
    # Create client interface  
    client = LANMultiplayerInterface(host=False, server_ip=server_ip, port=7777)
    
    # Set up chat message handler
    def handle_chat(data):
        player = data.get('player')
        message = data.get('message')
        print(f"CLIENT received: [Player {player}] {message}")
        message_log.add_player_message(player, message)
    
    client.register_message_handler(MessageType.CHAT, handle_chat)
    
    # Initialize connection
    print(f"CLIENT: Connecting to {server_ip}:7777...")
    if client.initialize():
        print("CLIENT: Connected to host!")
        
        # Send a test message
        time.sleep(2)
        print("CLIENT: Sending test message...")
        success = client.send_message(MessageType.CHAT, {
            "player": 2,
            "message": "Hello from client!"
        })
        print(f"CLIENT: Message send {'successful' if success else 'failed'}")
        
        # Process messages for 8 seconds
        start_time = time.time()
        while time.time() - start_time < 8:
            client.receive_messages()
            time.sleep(0.1)
            
    else:
        print("CLIENT: Failed to connect!")
    
    client.cleanup()
    print("CLIENT: Cleanup complete")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 test_lan_chat.py host           # Test as host")
        print("  python3 test_lan_chat.py client [ip]    # Test as client")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "host":
        test_host()
    elif mode == "client":
        server_ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        test_client(server_ip)
    else:
        print("Invalid mode. Use 'host' or 'client'")
        sys.exit(1)