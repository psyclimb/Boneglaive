#!/usr/bin/env python3
"""
Test script for Boneglaive map implementation.
This script tests the map and terrain functionality without running the full game.
"""

from boneglaive.game.map import GameMap, MapFactory, TerrainType
from boneglaive.game.engine import Game
from boneglaive.utils.coordinates import Position

def test_map_creation():
    """Test creating a map and checking terrain."""
    # Create the Lime Foyer map
    lime_map = MapFactory.create_map("lime_foyer")
    
    # Verify map name
    print(f"Map name: {lime_map.name}")
    assert lime_map.name == "The Lime Foyer", f"Expected 'The Lime Foyer', got '{lime_map.name}'"
    
    # Get counts of each terrain type
    terrain_counts = {
        TerrainType.EMPTY: 0, 
        TerrainType.LIMESTONE: 0,
        TerrainType.DUST: 0,
        TerrainType.PILLAR: 0,
        TerrainType.FURNITURE: 0
    }
    
    for y in range(lime_map.height):
        for x in range(lime_map.width):
            terrain = lime_map.get_terrain_at(y, x)
            terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
    
    # Print terrain distribution
    print("Terrain distribution:")
    for terrain, count in terrain_counts.items():
        print(f"  {terrain.name}: {count} tiles")
    
    # Verify terrain exists
    assert terrain_counts[TerrainType.LIMESTONE] > 0, "Expected limestone terrain to exist"
    assert terrain_counts[TerrainType.DUST] > 0, "Expected dust terrain to exist"
    assert terrain_counts[TerrainType.PILLAR] > 0, "Expected pillar terrain to exist"
    assert terrain_counts[TerrainType.FURNITURE] > 0, "Expected furniture terrain to exist"
    assert terrain_counts[TerrainType.EMPTY] > 0, "Expected empty terrain to exist"
    
    print("Map creation test passed!\n")

def test_terrain_effects():
    """Test terrain effects on movement and unit placement."""
    game = Game(skip_setup=True)
    
    # Count passable vs impassable tiles
    passable = 0
    impassable = 0
    
    for y in range(game.map.height):
        for x in range(game.map.width):
            if game.map.is_passable(y, x):
                passable += 1
            else:
                impassable += 1
    
    print(f"Passable tiles: {passable}")
    print(f"Impassable tiles: {impassable}")
    
    # Get the positions of impassable tiles
    impassable_positions = []
    for y in range(game.map.height):
        for x in range(game.map.width):
            if not game.map.is_passable(y, x):
                impassable_positions.append((y, x))
    
    print(f"First few impassable positions: {impassable_positions[:5]}")
    
    # Check that default units were not placed on impassable terrain
    print("\nVerifying units aren't on impassable terrain:")
    for unit in game.units:
        terrain = game.map.get_terrain_at(unit.y, unit.x)
        print(f"Unit at ({unit.y}, {unit.x}): Terrain = {terrain.name}, Passable = {game.map.is_passable(unit.y, unit.x)}")
        assert game.map.is_passable(unit.y, unit.x), f"Unit at ({unit.y}, {unit.x}) is on impassable terrain"
    
    # Test unit movement validation
    if game.units:
        unit = game.units[0]
        print(f"\nTesting movement for unit at ({unit.y}, {unit.x}):")
        
        # Try to move to an adjacent position
        adjacent_positions = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                new_y, new_x = unit.y + dy, unit.x + dx
                if game.is_valid_position(new_y, new_x):
                    adjacent_positions.append((new_y, new_x))
        
        for pos_y, pos_x in adjacent_positions:
            terrain = game.map.get_terrain_at(pos_y, pos_x)
            can_move = game.can_move_to(unit, pos_y, pos_x)
            occupied = game.get_unit_at(pos_y, pos_x) is not None
            print(f"  Can move to ({pos_y}, {pos_x})? {can_move} - Terrain: {terrain.name}, Passable: {game.map.is_passable(pos_y, pos_x)}, Occupied: {occupied}")
            
            # Verify can_move_to respects terrain and unit occupancy
            expected = game.map.is_passable(pos_y, pos_x) and not occupied
            assert can_move == expected, f"Movement validation doesn't match combined terrain+occupancy check"
    
    print("Terrain effects test passed!")

if __name__ == "__main__":
    print("Testing Boneglaive Map Implementation\n")
    
    test_map_creation()
    test_terrain_effects()
    
    print("\nAll tests passed successfully!")