#!/usr/bin/env python3
"""
Test script to verify Heinous Vapor expiration with invulnerability.
"""

from boneglaive.utils.constants import UnitType
from boneglaive.game.units import Unit

def test_vapor_expiration():
    # Create a Heinous Vapor unit
    vapor = Unit(UnitType.HEINOUS_VAPOR, player=1, y=0, x=0)
    
    # Set invulnerability flag
    vapor.is_invulnerable = True
    
    # Initialize HP
    initial_hp = vapor.hp
    print(f"Initial HP: {initial_hp}")
    
    # Try to damage the vapor (should be blocked)
    vapor.hp = 1
    print(f"HP after damage attempt: {vapor.hp}")
    
    # Use expire() method to simulate duration expiration (should bypass invulnerability)
    vapor.expire()
    print(f"HP after expire(): {vapor.hp}")
    
    # Check is_alive() status
    print(f"Is vapor alive?: {vapor.is_alive()}")
    
    # Test result
    if vapor.hp == 0 and not vapor.is_alive():
        print("Test passed! The vapor was successfully expired despite invulnerability.")
    else:
        print("Test failed! The vapor could not be expired.")

if __name__ == "__main__":
    test_vapor_expiration()