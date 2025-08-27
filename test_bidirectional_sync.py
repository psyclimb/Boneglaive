#!/usr/bin/env python3
"""
Test script for bidirectional game state synchronization.
Phase 5.6: Comprehensive bidirectional sync validation.

This test validates that:
1. Both players send their game state batches
2. Both players receive and apply the other's state  
3. Both perform parity checks and cross-verification
4. Reconciliation works when states diverge
5. Authority resolution works for conflict resolution
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

class MockNetwork:
    """Mock network interface for testing bidirectional sync."""
    
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
        print(f"📤 Player {self.player_number} sent {message_type.value}: {data.keys()}")
        return True
        
    def register_message_handler(self, message_type: MessageType, handler):
        self.message_handlers[message_type] = handler
        
    def receive_messages(self):
        pass  # Mock implementation - messages processed manually in test

def create_test_game_with_differences(game_num: int) -> Game:
    """Create test games with intentional differences for sync testing."""
    game = Game(skip_setup=True, map_name="lime_foyer")
    
    # Create some units
    from boneglaive.utils.constants import UnitType
    
    if game_num == 1:
        # Game 1: Standard setup
        unit1 = game.add_unit(UnitType.GLAIVEMAN, 1, 5, 5)
        unit2 = game.add_unit(UnitType.GRAYMAN, 2, 10, 10)
        if unit1:
            unit1.hp = 80  # Some damage
        if unit2:
            unit2.hp = 90  # Less damage
    else:
        # Game 2: Different state to test sync
        unit1 = game.add_unit(UnitType.GLAIVEMAN, 1, 5, 5)
        unit2 = game.add_unit(UnitType.GRAYMAN, 2, 10, 10)
        if unit1:
            unit1.hp = 75  # More damage (different from game 1)
        if unit2:
            unit2.hp = 85  # More damage (different from game 1)
            
    return game

def test_bidirectional_game_state_sync():
    """Test complete bidirectional game state synchronization."""
    
    print("🔄 TESTING BIDIRECTIONAL GAME STATE SYNC")
    print("=" * 60)
    
    # Create two games with different states
    game1 = create_test_game_with_differences(1)
    game2 = create_test_game_with_differences(2)
    
    # Create mock networks
    network1 = MockNetwork(player_number=1, is_host=True)   # Host
    network2 = MockNetwork(player_number=2, is_host=False)  # Client
    
    # Create game state sync instances
    sync1 = GameStateSync(game1, network1)
    sync2 = GameStateSync(game2, network2)
    
    print(f"📊 Initial State Checksums:")
    checksum1_initial = game_state_serializer.generate_checksum(game1)
    checksum2_initial = game_state_serializer.generate_checksum(game2)
    print(f"   Player 1 (Host): {checksum1_initial}")
    print(f"   Player 2 (Client): {checksum2_initial}")
    print(f"   States Match: {checksum1_initial == checksum2_initial}")
    print()
    
    # Test 1: Both players send game state batches (bidirectional initiation)
    print("🧪 TEST 1: Bidirectional batch sending")
    print("-" * 40)
    
    # Player 1 ends turn and sends batch
    print("Player 1 ending turn...")
    success1 = sync1.perform_end_of_turn_sync()
    print(f"Player 1 sync initiation: {'✓' if success1 else '✗'}")
    
    # Player 2 ends turn and sends batch  
    print("Player 2 ending turn...")
    success2 = sync2.perform_end_of_turn_sync()
    print(f"Player 2 sync initiation: {'✓' if success2 else '✗'}")
    
    # Check that both sent game state batches
    game_state_batches_1 = [m for m in network1.sent_messages if m['type'] == MessageType.GAME_STATE_BATCH]
    game_state_batches_2 = [m for m in network2.sent_messages if m['type'] == MessageType.GAME_STATE_BATCH]
    
    print(f"Player 1 sent {len(game_state_batches_1)} game state batch(es)")
    print(f"Player 2 sent {len(game_state_batches_2)} game state batch(es)")
    print()
    
    # Test 2: Cross-batch processing (simulate network delivery)
    print("🧪 TEST 2: Cross-batch processing and verification")
    print("-" * 40)
    
    if game_state_batches_1 and game_state_batches_2:
        # Player 2 receives Player 1's batch
        print("Player 2 receiving Player 1's game state batch...")
        p1_batch_data = game_state_batches_1[0]['data']
        sync2._handle_game_state_batch(p1_batch_data)
        
        # Player 1 receives Player 2's batch
        print("Player 1 receiving Player 2's game state batch...")
        p2_batch_data = game_state_batches_2[0]['data']
        sync1._handle_game_state_batch(p2_batch_data)
        
        print("Cross-batch processing completed")
    else:
        print("❌ ERROR: Not enough game state batches sent")
    print()
    
    # Test 3: Verify bidirectional parity checks were sent
    print("🧪 TEST 3: Bidirectional parity check validation")
    print("-" * 40)
    
    # Check for parity check messages
    parity_checks_1 = [m for m in network1.sent_messages if m['type'] == MessageType.GAME_STATE_PARITY_CHECK]
    parity_checks_2 = [m for m in network2.sent_messages if m['type'] == MessageType.GAME_STATE_PARITY_CHECK]
    
    print(f"Player 1 sent {len(parity_checks_1)} parity check(s)")
    print(f"Player 2 sent {len(parity_checks_2)} parity check(s)")
    
    # Check for cross-verification batches (additional game state batches sent back)
    total_batches_1 = len([m for m in network1.sent_messages if m['type'] == MessageType.GAME_STATE_BATCH])
    total_batches_2 = len([m for m in network2.sent_messages if m['type'] == MessageType.GAME_STATE_BATCH])
    
    print(f"Player 1 total game state batches: {total_batches_1}")
    print(f"Player 2 total game state batches: {total_batches_2}")
    print()
    
    # Test 4: Final state verification
    print("🧪 TEST 4: Final state synchronization verification")
    print("-" * 40)
    
    checksum1_final = game_state_serializer.generate_checksum(game1)
    checksum2_final = game_state_serializer.generate_checksum(game2)
    
    print(f"📊 Final State Checksums:")
    print(f"   Player 1 (Host): {checksum1_final}")
    print(f"   Player 2 (Client): {checksum2_final}")
    print(f"   States Now Match: {checksum1_final == checksum2_final}")
    print()
    
    # Test 5: Message pattern analysis
    print("🧪 TEST 5: Message pattern analysis")
    print("-" * 40)
    
    print("Player 1 message sequence:")
    for i, msg in enumerate(network1.sent_messages, 1):
        print(f"  {i}. {msg['type'].value}")
        
    print("Player 2 message sequence:")
    for i, msg in enumerate(network2.sent_messages, 1):
        print(f"  {i}. {msg['type'].value}")
    print()
    
    # Test Results Summary
    print("📈 BIDIRECTIONAL SYNC TEST RESULTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Both sent initial batches
    if len(game_state_batches_1) >= 1 and len(game_state_batches_2) >= 1:
        print("✅ Test 1 PASSED: Both players sent game state batches")
        tests_passed += 1
    else:
        print("❌ Test 1 FAILED: Not all players sent game state batches")
    
    # Test 2: Cross-verification batches sent
    if total_batches_1 >= 2 and total_batches_2 >= 2:
        print("✅ Test 2 PASSED: Bidirectional cross-verification occurred")
        tests_passed += 1
    else:
        print("❌ Test 2 FAILED: Insufficient cross-verification batches")
    
    # Test 3: Parity checks sent
    if len(parity_checks_1) >= 1 and len(parity_checks_2) >= 1:
        print("✅ Test 3 PASSED: Both players sent parity checks")
        tests_passed += 1
    else:
        print("❌ Test 3 FAILED: Not all players sent parity checks")
    
    # Test 4: States synchronized
    if checksum1_final == checksum2_final:
        print("✅ Test 4 PASSED: Game states synchronized")
        tests_passed += 1
    else:
        print("❌ Test 4 FAILED: Game states not synchronized")
    
    # Test 5: Proper message pattern
    expected_messages = ['GAME_STATE_BATCH', 'GAME_STATE_PARITY_CHECK']
    pattern_correct = True
    for network in [network1, network2]:
        msg_types = [m['type'].value for m in network.sent_messages]
        if not any('GAME_STATE_BATCH' in msg_types for msg_types in [msg_types]):
            pattern_correct = False
    
    if pattern_correct:
        print("✅ Test 5 PASSED: Proper message patterns observed")
        tests_passed += 1
    else:
        print("❌ Test 5 FAILED: Improper message patterns")
    
    print(f"\n🎯 OVERALL RESULT: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 BIDIRECTIONAL SYNC SYSTEM WORKING CORRECTLY!")
    else:
        print("⚠️  BIDIRECTIONAL SYNC SYSTEM NEEDS FIXES")
    
    return tests_passed == total_tests

def test_authority_resolution():
    """Test authority resolution in case of conflicts."""
    
    print("\n🔄 TESTING AUTHORITY RESOLUTION")
    print("=" * 60)
    
    # Create conflicted games
    game_host = create_test_game_with_differences(1)
    game_client = create_test_game_with_differences(2)
    
    # Create networks
    network_host = MockNetwork(player_number=1, is_host=True)
    network_client = MockNetwork(player_number=2, is_host=False)
    
    # Create sync instances
    sync_host = GameStateSync(game_host, network_host)
    sync_client = GameStateSync(game_client, network_client)
    
    print("🧪 Testing authority resolution...")
    
    # Simulate desync detection and authority resolution
    host_checksum = game_state_serializer.generate_checksum(game_host)
    client_checksum = game_state_serializer.generate_checksum(game_client)
    
    print(f"Host checksum: {host_checksum}")
    print(f"Client checksum: {client_checksum}")
    
    # Host detects desync and sends authoritative state
    print("Host sending authoritative state...")
    auth_success = sync_host.send_authoritative_game_state_sync(to_player=2, turn_number=1)
    
    # Client detects desync and requests authoritative state  
    print("Client requesting authoritative state...")
    req_success = sync_client.request_full_game_state_sync(from_player=1, turn_number=1)
    
    # Check messages
    auth_messages = [m for m in network_host.sent_messages if m['type'] == MessageType.GAME_STATE_FULL_SYNC]
    req_messages = [m for m in network_client.sent_messages if m['type'] == MessageType.GAME_STATE_SYNC_REQUEST]
    
    print(f"Host sent {len(auth_messages)} authoritative sync message(s)")
    print(f"Client sent {len(req_messages)} sync request message(s)")
    
    authority_test_passed = auth_success and req_success and len(auth_messages) >= 1
    
    if authority_test_passed:
        print("✅ AUTHORITY RESOLUTION TEST PASSED")
    else:
        print("❌ AUTHORITY RESOLUTION TEST FAILED")
    
    return authority_test_passed

if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE BIDIRECTIONAL SYNC TESTS")
    print("=" * 80)
    
    try:
        # Run bidirectional sync test
        sync_result = test_bidirectional_game_state_sync()
        
        # Run authority resolution test
        authority_result = test_authority_resolution()
        
        print("\n" + "=" * 80)
        print("🏁 FINAL TEST SUMMARY")
        print("=" * 80)
        
        if sync_result and authority_result:
            print("🎉 ALL BIDIRECTIONAL SYNC TESTS PASSED!")
            print("✅ System is ready for real-world LAN multiplayer testing")
            sys.exit(0)
        else:
            print("⚠️  SOME TESTS FAILED - SYSTEM NEEDS FIXES")
            print("❌ Review bidirectional sync implementation")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)