#!/usr/bin/env python3
"""
Quick test of simplified PELOTARI ricochet physics.
"""

import sys
sys.path.insert(0, '/home/user/boneglaive')

from boneglaive.dlc.pelotari.physics import calculate_bounce

class MockGame:
    """Mock game for testing."""
    def __init__(self):
        self.map_layout = [
            [False, False, False, False, False],
            [False, True,  True,  True,  False],
            [False, True,  True,  True,  False],
            [False, True,  True,  True,  False],
            [False, False, False, False, False],
        ]

    def is_valid_position(self, y, x):
        return 0 <= y < 5 and 0 <= x < 5

    class Map:
        def __init__(self, layout):
            self.layout = layout

        def is_passable(self, y, x):
            return self.layout[y][x]

    def __init__(self):
        layout = [
            [False, False, False, False, False],  # Top wall
            [False, True,  True,  True,  False],  # Open middle
            [False, True,  True,  True,  False],  # Open middle
            [False, True,  True,  True,  False],  # Open middle
            [False, False, False, False, False],  # Bottom wall
        ]
        self.map = self.Map(layout)

def test_bounces():
    """Test different bounce scenarios."""
    game = MockGame()

    print("Testing simplified mirror reflection physics:\n")

    # Test 1: Ball traveling left hits left wall
    print("Test 1: Ball at (1,2) traveling left hits left wall at (1,0)")
    impact = (1, 0)  # Left wall position
    direction = (0, -1)  # Traveling left (toward the wall)
    result = calculate_bounce(impact, direction, game)
    print(f"  Direction: {direction} -> {result}")
    print(f"  Expected: (0, 1) [bounce back right]")
    print(f"  Match: {result == (0, 1)}\n")

    # Test 2: Ball traveling up hits top wall
    print("Test 2: Ball at (2,2) traveling up hits top wall at (0,2)")
    impact = (0, 2)  # Top wall position
    direction = (-1, 0)  # Traveling up (toward the wall)
    result = calculate_bounce(impact, direction, game)
    print(f"  Direction: {direction} -> {result}")
    print(f"  Expected: (1, 0) [bounce back down]")
    print(f"  Match: {result == (1, 0)}\n")

    # Test 3: Ball traveling diagonally NE hits top-right corner
    print("Test 3: Ball traveling NE hits top-right corner")
    impact = (0, 4)  # Top-right corner
    direction = (-1, 1)  # Traveling NE
    result = calculate_bounce(impact, direction, game)
    print(f"  Direction: {direction} -> {result}")
    print(f"  Expected: (1, -1) [reverse both - bounce back diagonally]")
    print(f"  Match: {result == (1, -1)}\n")

    # Test 4: Ball traveling diagonally NE hits right wall near corner
    print("Test 4: Ball at (2,2) traveling NE hits right wall at (1,4)")
    impact = (1, 4)  # Right wall near top-right corner
    direction = (-1, 1)  # Traveling NE (up-right)
    result = calculate_bounce(impact, direction, game)
    print(f"  Direction: {direction} -> {result}")
    print(f"  Expected: (1, -1) [bounce back SW - both components flip]")
    print(f"  Note: Can't continue up (wall at 0,4) or right (out of bounds)")
    print(f"  Match: {result == (1, -1)}\n")

    print("All tests completed!")
    print("\nSimplified physics rules:")
    print("- Vertical wall (|): flip horizontal (dx = -dx)")
    print("- Horizontal wall (—): flip vertical (dy = -dy)")
    print("- Corner: flip both (-dy, -dx)")

if __name__ == '__main__':
    test_bounces()
