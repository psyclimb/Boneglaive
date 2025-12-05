#!/usr/bin/env python3
"""
Test script to verify rail graphics system without requiring display.
"""
import sys
sys.path.insert(0, '/home/user/boneglaive')

from boneglaive.game.map import GameMap, TerrainType

def test_rail_type_detection():
    """Test the get_rail_type() method logic."""
    print("Testing rail type detection logic...")

    # Create a test map
    game_map = GameMap(height=10, width=20)

    # Simulate rail network generation
    print("\n1. Generating rail network...")
    game_map.generate_rail_network()

    rail_positions = game_map.get_rail_positions()
    print(f"   Total rails placed: {len(rail_positions)}")

    # Test rail type detection at various positions
    print("\n2. Testing rail type detection:")

    # Test a few specific positions
    test_positions = [
        (3, 8),   # Should be on horizontal line (row 3, col 8 - vertical line)
        (3, 10),  # Should be on horizontal line  (row 3, arbitrary col)
        (5, 8),   # Should be on vertical line (col 8)
        (5, 12),  # Should be on vertical line (col 12)
    ]

    for y, x in test_positions:
        if game_map.get_terrain_at(y, x) == TerrainType.RAIL:
            rail_type = game_map.get_rail_type(y, x)

            # Check neighbors for context
            has_n = y > 0 and game_map.get_terrain_at(y-1, x) == TerrainType.RAIL
            has_s = y < 9 and game_map.get_terrain_at(y+1, x) == TerrainType.RAIL
            has_e = x < 19 and game_map.get_terrain_at(y, x+1) == TerrainType.RAIL
            has_w = x > 0 and game_map.get_terrain_at(y, x-1) == TerrainType.RAIL

            neighbors = []
            if has_n: neighbors.append("N")
            if has_s: neighbors.append("S")
            if has_e: neighbors.append("E")
            if has_w: neighbors.append("W")

            print(f"   Position ({y},{x}): type='{rail_type}', neighbors={','.join(neighbors) if neighbors else 'none'}")

    # Count rail types
    print("\n3. Rail type distribution:")
    type_counts = {"ns": 0, "ew": 0, "cross": 0}

    for y, x in rail_positions:
        rail_type = game_map.get_rail_type(y, x)
        type_counts[rail_type] += 1

    print(f"   NS (vertical):      {type_counts['ns']}")
    print(f"   EW (horizontal):    {type_counts['ew']}")
    print(f"   CROSS (junction):   {type_counts['cross']}")

    # Visual map representation
    print("\n4. Rail network visualization:")
    print("   (N=NS rail, E=EW rail, X=Cross junction, .=empty)")
    print()

    for y in range(10):
        row = "   "
        for x in range(20):
            terrain = game_map.get_terrain_at(y, x)
            if terrain == TerrainType.RAIL:
                rail_type = game_map.get_rail_type(y, x)
                if rail_type == "ns":
                    row += "N"
                elif rail_type == "ew":
                    row += "E"
                elif rail_type == "cross":
                    row += "X"
            else:
                row += "."
        print(row)

    print("\n✓ Rail type detection test completed successfully!")

if __name__ == "__main__":
    test_rail_type_detection()
