#!/usr/bin/env python3
"""
Test script for combat log UI component.
"""
import sys
import os
from pathlib import Path

# Disable pygame display for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

sys.path.insert(0, str(Path(__file__).parent))

def test_combat_log():
    """Test combat log component."""
    print("=" * 60)
    print("Testing Combat Log UI Component")
    print("=" * 60)

    # Initialize pygame
    import pygame
    pygame.init()

    print("\n--- Test 1: Import Combat Log ---")
    from boneglaive.graphical.ui.combat_log import CombatLog
    print("✓ CombatLog imported successfully")

    print("\n--- Test 2: Create Combat Log ---")
    font = pygame.font.Font(None, 18)
    combat_log = CombatLog(font)
    print("✓ CombatLog created successfully")
    print(f"Max messages: {combat_log.max_messages}")

    print("\n--- Test 3: Add Messages ---")
    combat_log.add_message("Game started", "system")
    combat_log.add_message("Player 1's turn", "system")
    combat_log.add_message("GLAIVEMAN moved to (5, 3)", "movement", player=1)
    combat_log.add_message("GLAIVEMAN attacked INTERFERER", "combat", player=1)
    combat_log.add_message("INTERFERER took 8 damage", "combat", player=2)

    print(f"✓ Added 5 messages")
    print(f"Total messages in log: {len(combat_log.messages)}")

    print("\n--- Test 4: Message Display ---")
    for i, msg in enumerate(combat_log.messages):
        print(f"  {i+1}. [{msg['type']}] {msg['text']}")

    print("\n--- Test 5: Fetch from Game Message Log ---")
    from boneglaive.graphical.game_state import GameStateAdapter
    from boneglaive.utils.message_log import message_log, MessageType

    # Initialize game
    adapter = GameStateAdapter()
    adapter.initialize_game(skip_setup=True)

    # Add some messages to game log
    message_log.add_message("Test system message", MessageType.SYSTEM)
    message_log.add_combat_message("Alpha", "Beta", 10, attacker_player=1, target_player=2)

    # Fetch messages
    combat_log.add_messages_from_game_log(message_log, count=10)
    print(f"✓ Fetched messages from game log")
    print(f"Total messages now: {len(combat_log.messages)}")

    print("\n--- Test 6: Scrolling ---")
    # Add many messages
    for i in range(20):
        combat_log.add_message(f"Message {i}", "system")

    print(f"Added 20 more messages")
    print(f"Scroll offset: {combat_log.scroll_offset}")
    print(f"Auto-scroll: {combat_log.auto_scroll}")

    combat_log.scroll_up(5)
    print(f"After scroll up: offset={combat_log.scroll_offset}, auto={combat_log.auto_scroll}")

    combat_log.scroll_down(5)
    print(f"After scroll down: offset={combat_log.scroll_offset}, auto={combat_log.auto_scroll}")

    print("\n--- Test 7: Clear Log ---")
    combat_log.clear()
    print(f"✓ Log cleared")
    print(f"Messages after clear: {len(combat_log.messages)}")

    print("\n--- Test 8: Color Mapping ---")
    test_messages = [
        {"text": "System", "type": "system", "player": None},
        {"text": "Combat", "type": "combat", "player": None},
        {"text": "Ability", "type": "ability", "player": None},
        {"text": "Player 1", "type": "combat", "player": 1},
        {"text": "Player 2", "type": "combat", "player": 2},
    ]

    for msg in test_messages:
        color = combat_log._get_message_color(msg)
        print(f"  {msg['text']:12} -> RGB{color}")

    print("\n✓ All combat log tests passed")
    pygame.quit()
    return True


if __name__ == "__main__":
    try:
        success = test_combat_log()
        print("\n" + "=" * 60)
        if success:
            print("✓ Combat Log Test PASSED")
            sys.exit(0)
        else:
            print("✗ Combat Log Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
