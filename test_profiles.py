#!/usr/bin/env python3
"""
Test script for player profile system.
Demonstrates basic profile operations.
"""

from boneglaive.game.player_profile import profile_manager
from boneglaive.utils.constants import UnitType


def test_profiles():
    """Test basic profile operations."""
    print("=== Player Profile System Test ===\n")

    # Create a test profile
    print("1. Creating profile 'TESTUSER'...")
    try:
        profile = profile_manager.create_profile("TestUser")  # Will be converted to 'TESTUSER'
        print(f"   ✓ Created profile: {profile.name}")
    except ValueError as e:
        print(f"   Profile already exists, loading...")
        profile = profile_manager.load_profile("TESTUSER")

    # Set as current profile
    profile_manager.set_current_profile(profile)
    print(f"   ✓ Set as current profile\n")

    # Record some games
    print("2. Recording game results...")
    profile.record_win()
    profile.record_win()
    profile.record_loss()
    profile_manager.save_profile(profile)
    print(f"   ✓ Record: {profile.wins}W - {profile.losses}L")
    print(f"   ✓ Win rate: {profile.get_win_rate():.1f}%\n")

    # Record unit picks
    print("3. Recording unit selections...")
    profile.record_unit_pick(UnitType.GRAYMAN)
    profile.record_unit_pick(UnitType.GRAYMAN)
    profile.record_unit_pick(UnitType.INTERFERER)
    profile.record_unit_pick(UnitType.GLAIVEMAN)
    profile_manager.save_profile(profile)
    print(f"   ✓ Most picked: {profile.get_most_picked_unit()}")
    print(f"   ✓ GRAYMAN: {profile.unit_picks['GRAYMAN']} picks")
    print(f"   ✓ INTERFERER: {profile.unit_picks['INTERFERER']} picks\n")

    # Test name length limit
    print("4. Testing 8 character limit...")
    try:
        long_profile = profile_manager.create_profile("VERYLONGNAME123")
        print(f"   ✓ Name truncated to: '{long_profile.name}' (8 chars)")
        profile_manager.delete_profile(long_profile.name)
    except ValueError:
        print(f"   Profile existed, skipping...\n")

    # List all profiles
    print("5. Listing all profiles...")
    profiles = profile_manager.list_profiles()
    for name in profiles:
        p = profile_manager.load_profile(name)
        print(f"   - {name}: {p.wins}W-{p.losses}L ({p.games_played} games)")

    print("\n=== Test Complete ===")
    print(f"Profile saved to: profiles/{profile.name}.json")


if __name__ == "__main__":
    test_profiles()
