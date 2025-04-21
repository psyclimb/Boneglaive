#!/usr/bin/env python3
"""
Map system for Boneglaive - includes map generation and terrain effects.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Set

from boneglaive.utils.constants import HEIGHT, WIDTH
from boneglaive.utils.coordinates import Position


class TerrainType(Enum):
    """Types of terrain that can appear on the map."""
    EMPTY = 0      # Basic empty tile, no effects
    LIMESTONE = 1  # Limestone formation, blocks movement and unit placement
    DUST = 2       # Light limestone dusting, visual only (passable)
    PILLAR = 3     # Large limestone pillar, blocks movement and unit placement
    FURNITURE = 4  # Generic furniture, blocks movement but not line of sight
    COAT_RACK = 5  # Coat rack, blocks movement but not line of sight
    BENCH = 6      # Bench/ottoman seating, blocks movement but not line of sight
    CONSOLE = 7    # Console table, blocks movement but not line of sight
    DEC_TABLE = 8  # Decorative table, blocks movement but not line of sight


class GameMap:
    """Base class for game maps with terrain information."""
    
    def __init__(self, height: int = HEIGHT, width: int = WIDTH):
        self.height = height
        self.width = width
        self.terrain: Dict[Tuple[int, int], TerrainType] = {}
        self.name = "Generic Map"
        
        # Generate an empty map by default
        self.reset_to_empty()
    
    def reset_to_empty(self) -> None:
        """Reset the map to all empty terrain."""
        self.terrain = {}
        for y in range(self.height):
            for x in range(self.width):
                self.terrain[(y, x)] = TerrainType.EMPTY
    
    def get_terrain_at(self, y: int, x: int) -> TerrainType:
        """Get terrain type at the given coordinates."""
        return self.terrain.get((y, x), TerrainType.EMPTY)
    
    def set_terrain_at(self, y: int, x: int, terrain_type: TerrainType) -> None:
        """Set terrain type at the given coordinates."""
        self.terrain[(y, x)] = terrain_type
    
    def is_passable(self, y: int, x: int) -> bool:
        """Check if a position is passable (can be moved through)."""
        terrain = self.get_terrain_at(y, x)
        # All furniture types (including the new ones) are impassable, like pillars and limestone
        return terrain in [TerrainType.EMPTY, TerrainType.DUST]
    
    def can_place_unit(self, y: int, x: int) -> bool:
        """Check if a unit can be placed at this position."""
        terrain = self.get_terrain_at(y, x)
        # Units can only be placed on empty or dusty tiles, not on any type of furniture
        return terrain in [TerrainType.EMPTY, TerrainType.DUST]
        
    def blocks_line_of_sight(self, y: int, x: int) -> bool:
        """Check if a position blocks line of sight for ranged attacks."""
        terrain = self.get_terrain_at(y, x)
        # Only limestone and pillars block line of sight - furniture doesn't
        return terrain in [TerrainType.LIMESTONE, TerrainType.PILLAR]


class LimeFoyerMap(GameMap):
    """The Lime Foyer map with pillars, furniture and windswept dust patterns."""
    
    def __init__(self):
        super().__init__()
        self.name = "The Lime Foyer"
        self.generate_map()
    
    def generate_map(self) -> None:
        """Generate the enhanced Lime Foyer map based on the mockup."""
        # Reset to empty first
        self.reset_to_empty()
        
        # Large limestone powder piles (block movement)
        limestone_piles = [
            (1, 2), (1, 3), (1, 16), (1, 17),  # Top edge piles
            (2, 1), (2, 18),                    # Side piles
            (4, 0), (6, 19),                    # More side piles
            (6, 2), (7, 3),                     # Left side piles
            (9, 0), (9, 1), (9, 13), (9, 15)    # Bottom piles
        ]
        for y, x in limestone_piles:
            self.set_terrain_at(y, x, TerrainType.LIMESTONE)
        
        # Top round pillar (3x3)
        pillar_top = [
            (2, 7), (2, 8), (2, 9),
            (3, 7), (3, 8), (3, 9),
            (4, 7), (4, 8), (4, 9)
        ]
        for y, x in pillar_top:
            self.set_terrain_at(y, x, TerrainType.PILLAR)
            
        # Bottom round pillar (3x5)
        pillar_bottom = [
            (7, 7), (7, 8), (7, 9), (7, 10), (7, 11),
            (8, 7), (8, 8), (8, 9), (8, 10), (8, 11),
            (9, 7), (9, 8), (9, 9), (9, 10), (9, 11)
        ]
        for y, x in pillar_bottom:
            self.set_terrain_at(y, x, TerrainType.PILLAR)
        
        # Furniture pieces
        # Coat racks
        self.set_terrain_at(0, 5, TerrainType.COAT_RACK)  # Left coat rack
        self.set_terrain_at(0, 14, TerrainType.COAT_RACK) # Right coat rack
        
        # Console table
        self.set_terrain_at(4, 3, TerrainType.CONSOLE)  # Entry console
        
        # Benches/Ottomans
        self.set_terrain_at(5, 13, TerrainType.BENCH) # Middle bench
        self.set_terrain_at(8, 13, TerrainType.BENCH) # Bottom bench
        
        # Decorative tables
        self.set_terrain_at(0, 10, TerrainType.DEC_TABLE) # Top table
        self.set_terrain_at(4, 16, TerrainType.DEC_TABLE) # Right table
        
        # Light limestone dustings (windswept patterns)
        # This is a partial list - approximately 50% of tiles will have dust
        dust_patterns = [
            # Top row dust
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 6), (0, 7), (0, 15), (0, 16), (0, 17), (0, 18), (0, 19),
            
            # Second row dust
            (1, 0), (1, 1), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 19),
            
            # Third row dust
            (2, 0), (2, 2), (2, 3), (2, 6), (2, 10), (2, 11), (2, 12), (2, 14), (2, 15), (2, 17), (2, 19),
            
            # Fourth row dust
            (3, 0), (3, 1), (3, 4), (3, 10), (3, 11), (3, 12), (3, 13), (3, 17), (3, 18),
            
            # Fifth row dust
            (4, 1), (4, 2), (4, 4), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 17), (4, 18),
            
            # Sixth row dust
            (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 7), (5, 8), (5, 14), (5, 15), (5, 16), (5, 17), (5, 18),
            
            # Seventh row dust
            (6, 0), (6, 3), (6, 7), (6, 8), (6, 9), (6, 10), (6, 15), (6, 16), (6, 17), (6, 18),
            
            # Eighth row dust
            (7, 0), (7, 1), (7, 2), (7, 4), (7, 5), (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19),
            
            # Ninth row dust
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 12), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19),
            
            # Bottom row dust
            (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 12), (9, 14), (9, 16), (9, 17), (9, 18), (9, 19)
        ]
        
        for y, x in dust_patterns:
            # Only set dust if the tile is empty (not already a pillar, furniture, etc.)
            if self.get_terrain_at(y, x) == TerrainType.EMPTY:
                self.set_terrain_at(y, x, TerrainType.DUST)


class MapFactory:
    """Factory class for creating different maps."""
    
    @staticmethod
    def create_map(map_name: str) -> GameMap:
        """Create a map based on the given name."""
        if map_name.lower() == "lime_foyer":
            return LimeFoyerMap()
        else:
            # Default to empty map
            return GameMap()