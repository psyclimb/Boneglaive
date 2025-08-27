#!/usr/bin/env python3
"""
Test script specifically for Player 2 action execution and sync.
Verifies that P2→P1 sync works correctly.
"""

import sys
import os
import time
from unittest.mock import Mock, MagicMock

# Add the project root to Python path
sys.path.insert(0, '/home/jms/Projects/boneglaive2')

from boneglaive.game.engine import Game
from boneglaive.networking.game_state_sync import GameStateSync
from boneglaive.networking.game_state_serializer import game_state_serializer
from boneglaive.networking.network_interface import MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

class MockNetwork:
    """Mock network interface for testing P2 actions."""
    
    def __init__(self, player_number: int, is_host: bool = False):
        self.player_number = player_number
        self.is_host_flag = is_host
        self.sent_messages = []  # Track all sent messages
        self.message_handlers = {}
        self.connected = True
        
    def get_player_number(self) -> int:
        return self.player_number
        
    def is_host(self) -> bool:
        return self.is_host_flag
        
    def send_message(self, message_type: MessageType, data: dict) -> bool:
        message = {
            'type': message_type,
            'data': data,
            'timestamp': time.time(),
            'from_player': self.player_number
        }
        self.sent_messages.append(message)
        print(f"📤 Player {self.player_number} ({'Host' if self.is_host_flag else 'Client'}) sent {message_type.value}")
        return True
        
    def register_message_handler(self, message_type: MessageType, handler):
        self.message_handlers[message_type] = handler
        
    def receive_messages(self):
        pass  # Mock implementation - messages processed manually in test

def create_game_with_damaged_units():
    """Create a test game with units that can show visible changes."""
    game = Game(skip_setup=True, map_name="lime_foyer")
    
    # Add units for both players
    unit1 = game.add_unit(UnitType.GLAIVEMAN, 1, 5, 5)
    unit2 = game.add_unit(UnitType.GLAIVEMAN, 2, 10, 10)
    
    # Give units some damage so we can see changes
    if unit1:
        unit1.hp = 15  # Damaged from 22
        unit1.move_target = (6, 6)  # Give it a planned move
    if unit2:
        unit2.hp = 12  # Damaged from 22  
        unit2.move_target = (11, 11)  # Give it a planned move
        
    return game

def test_player2_action_execution():
    """Test that Player 2 actions are properly executed by the host."""
    
    print("🧪 TESTING PLAYER 2 ACTION EXECUTION")
    print("=" * 60)
    
    # Create games
    host_game = create_game_with_damaged_units()
    client_game = create_game_with_damaged_units()
    
    # Make client game different to simulate Player 2 making moves
    if len(client_game.units) >= 2:
        client_unit = client_game.units[1]  # Player 2's unit
        client_unit.move_target = (9, 9)  # Different move
        client_unit.hp = 10  # More damage
    
    # Create mock networks
    host_network = MockNetwork(player_number=1, is_host=True)   # Host (P1)
    client_network = MockNetwork(player_number=2, is_host=False)  # Client (P2)
    
    # Create sync instances
    host_sync = GameStateSync(host_game, host_network)
    client_sync = GameStateSync(client_game, client_network)
    
    print(f"📊 INITIAL STATE:")
    print(f"   Host game checksum: {game_state_serializer.generate_checksum(host_game)}")
    print(f"   Client game checksum: {game_state_serializer.generate_checksum(client_game)}")
    
    # Show initial unit states
    print(f"   Host P2 unit: HP={host_game.units[1].hp}, move_target={host_game.units[1].move_target}")
    print(f"   Client P2 unit: HP={client_game.units[1].hp}, move_target={client_game.units[1].move_target}")
    print()
    
    # Test 1: Player 2 sends end_turn action
    print("🧪 TEST 1: Player 2 sends end_turn action")
    print("-" * 40)
    
    # Simulate Player 2 ending their turn
    # Current player should be 2
    host_game.current_player = 2
    client_game.current_player = 2
    
    # Player 2 sends end_turn to host
    p2_end_turn_data = {
        "action_type": "end_turn",
        "data": {
            "planned_actions": []  # No planned actions for this test
        },
        "timestamp": time.time()
    }
    
    print("Player 2 (client) sending end_turn to host...")
    
    # Host receives Player 2's end_turn action
    host_sync._handle_player_action(p2_end_turn_data)
    
    print(f"✅ Host processed Player 2's end_turn action")
    print()
    
    # Test 2: Verify host state changed
    print("🧪 TEST 2: Verify host game state changed after P2's turn")
    print("-" * 40)
    
    print(f"📊 POST-EXECUTION STATE:")
    print(f"   Host game checksum: {game_state_serializer.generate_checksum(host_game)}")
    print(f"   Client game checksum: {game_state_serializer.generate_checksum(client_game)}")
    print(f"   Host current player: {host_game.current_player}")
    print(f"   Host turn number: {host_game.turn}")
    
    # Check if units moved (move_target should be None after execution)
    host_p2_unit = host_game.units[1]
    print(f"   Host P2 unit after turn: HP={host_p2_unit.hp}, position=({host_p2_unit.y},{host_p2_unit.x}), move_target={host_p2_unit.move_target}")
    
    # The unit should have moved and cleared its move_target
    if host_p2_unit.move_target is None:
        print("✅ Player 2's actions were executed (move_target cleared)")
    else:
        print("❌ Player 2's actions were NOT executed (move_target still set)")
    
    # Check turn transition
    if host_game.current_player == 1:  # Should switch back to P1
        print("✅ Turn transition worked correctly")
    else:
        print(f"❌ Turn transition failed - current_player={host_game.current_player}")
    print()
    
    # Test 3: Check message patterns
    print("🧪 TEST 3: Check message patterns from host")
    print("-" * 40)
    
    host_messages = [m['type'].value for m in host_network.sent_messages]
    print(f"Host sent messages: {host_messages}")
    
    # Host should send game state and messages to client
    expected_messages = ['message_log_batch', 'game_state_batch', 'turn_transition']
    messages_found = all(msg in host_messages for msg in expected_messages)
    
    if messages_found:
        print("✅ Host sent expected messages to client")
    else:
        print("❌ Host did not send all expected messages")
        print(f"   Expected: {expected_messages}")
        print(f"   Found: {host_messages}")
    print()
    
    # Test 4: Simulate applying host's state to client
    print("🧪 TEST 4: Apply host's game state to client")
    print("-" * 40)
    
    # Find the game state batch message
    game_state_messages = [m for m in host_network.sent_messages if m['type'] == MessageType.GAME_STATE_BATCH]
    
    if game_state_messages:
        # Apply the host's game state to the client
        host_state_data = game_state_messages[0]['data']
        print(f"Applying host's game state to client...")
        
        client_checksum_before = game_state_serializer.generate_checksum(client_game)
        
        # Apply host's state to client
        client_sync._handle_game_state_batch(host_state_data)
        
        client_checksum_after = game_state_serializer.generate_checksum(client_game)
        
        print(f"   Client checksum before: {client_checksum_before}")
        print(f"   Client checksum after: {client_checksum_after}")
        print(f"   Host checksum: {game_state_serializer.generate_checksum(host_game)}")
        
        # Check if client's P2 unit state matches host's
        client_p2_unit = client_game.units[1]
        print(f"   Client P2 unit after sync: HP={client_p2_unit.hp}, position=({client_p2_unit.y},{client_p2_unit.x})")
        
        # Check if states match
        if client_checksum_after == game_state_serializer.generate_checksum(host_game):
            print("✅ Client successfully synchronized with host's state")
        else:
            print("❌ Client did not synchronize properly with host")
    else:
        print("❌ No game state batch found from host")
    
    return True

if __name__ == "__main__":
    print("🚀 STARTING PLAYER 2 ACTION EXECUTION TEST")
    print("=" * 80)
    
    try:
        result = test_player2_action_execution()
        
        print("\n" + "=" * 80)
        print("🏁 PLAYER 2 ACTION TEST SUMMARY")
        print("=" * 80)
        
        if result:
            print("🎉 Player 2 action execution test completed!")
            print("   Check the output above to verify P2→P1 sync is working")
        else:
            print("❌ Player 2 action execution test failed")
            
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)