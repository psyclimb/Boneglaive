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
    EMPTY = 0     # Basic empty tile, no effects
    LIMESTONE = 1 # Limestone formation, blocks movement and unit placement


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
        return terrain == TerrainType.EMPTY
    
    def can_place_unit(self, y: int, x: int) -> bool:
        """Check if a unit can be placed at this position."""
        return self.is_passable(y, x)


class LimeFoyerMap(GameMap):
    """The Lime Foyer map with limestone formations."""
    
    def __init__(self):
        super().__init__()
        self.name = "The Lime Foyer"
        self.generate_map()
    
    def generate_map(self) -> None:
        """Generate the Lime Foyer map with limestone formations."""
        # Reset to empty first
        self.reset_to_empty()
        
        # Central limestone pillar
        self.set_terrain_at(4, 9, TerrainType.LIMESTONE)
        self.set_terrain_at(4, 10, TerrainType.LIMESTONE)
        self.set_terrain_at(5, 9, TerrainType.LIMESTONE)
        self.set_terrain_at(5, 10, TerrainType.LIMESTONE)
        
        # Left side limestone formations
        self.set_terrain_at(2, 5, TerrainType.LIMESTONE)
        self.set_terrain_at(2, 6, TerrainType.LIMESTONE)
        self.set_terrain_at(7, 5, TerrainType.LIMESTONE)
        self.set_terrain_at(7, 6, TerrainType.LIMESTONE)
        
        # Right side limestone formations
        self.set_terrain_at(2, 13, TerrainType.LIMESTONE)
        self.set_terrain_at(2, 14, TerrainType.LIMESTONE)
        self.set_terrain_at(7, 13, TerrainType.LIMESTONE)
        self.set_terrain_at(7, 14, TerrainType.LIMESTONE)
        
        # Top border formations
        for x in range(3, 17, 6):
            self.set_terrain_at(0, x, TerrainType.LIMESTONE)
            self.set_terrain_at(0, x+1, TerrainType.LIMESTONE)
        
        # Bottom border formations
        for x in range(3, 17, 6):
            self.set_terrain_at(9, x, TerrainType.LIMESTONE)
            self.set_terrain_at(9, x+1, TerrainType.LIMESTONE)
        
        # Add some scattered limestone deposits
        scattered_positions = [
            (1, 8), (1, 11),
            (8, 8), (8, 11),
            (4, 3), (5, 3),
            (4, 16), (5, 16)
        ]
        
        for y, x in scattered_positions:
            self.set_terrain_at(y, x, TerrainType.LIMESTONE)


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