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
    OTTOMAN = 6    # Ottoman seating, blocks movement but not line of sight
    CONSOLE = 7    # Console table, blocks movement but not line of sight
    DEC_TABLE = 8  # Decorative table, blocks movement but not line of sight
    MARROW_WALL = 9  # Marrow Dike wall, blocks movement and unit placement but not permanently
    RAIL = 10      # Rail track, passable by all units but FOWL_CONTRIVANCE gets special movement


class GameMap:
    """Base class for game maps with terrain information."""

    def __init__(self, height: int = HEIGHT, width: int = WIDTH):
        self.height = height
        self.width = width
        self.terrain: Dict[Tuple[int, int], TerrainType] = {}
        self.name = "Generic Map"

        # Dictionary to store cosmic values for furniture
        self.cosmic_values: Dict[Tuple[int, int], int] = {}

        # Generate an empty map by default
        self.reset_to_empty()

    def reset_to_empty(self) -> None:
        """Reset the map to all empty terrain."""
        self.terrain = {}
        for y in range(self.height):
            for x in range(self.width):
                self.terrain[(y, x)] = TerrainType.EMPTY

        # Reset cosmic values
        self.cosmic_values = {}
    
    def get_terrain_at(self, y: int, x: int) -> TerrainType:
        """Get terrain type at the given coordinates."""
        return self.terrain.get((y, x), TerrainType.EMPTY)
    
    def set_terrain_at(self, y: int, x: int, terrain_type: TerrainType) -> None:
        """Set terrain type at the given coordinates."""
        self.terrain[(y, x)] = terrain_type
    
    def is_passable(self, y: int, x: int) -> bool:
        """Check if a position is passable (can be moved through)."""
        terrain = self.get_terrain_at(y, x)
        # All furniture types, pillars, limestone, and marrow walls are impassable
        # Rails are passable by all units
        return terrain in [TerrainType.EMPTY, TerrainType.DUST, TerrainType.RAIL]
    
    def can_place_unit(self, y: int, x: int) -> bool:
        """Check if a unit can be placed at this position."""
        terrain = self.get_terrain_at(y, x)
        # Units can be placed on empty, dusty, or rail tiles
        return terrain in [TerrainType.EMPTY, TerrainType.DUST, TerrainType.RAIL]
        
    def blocks_line_of_sight(self, y: int, x: int) -> bool:
        """Check if a position blocks line of sight for ranged attacks."""
        terrain = self.get_terrain_at(y, x)
        # Limestone, pillars, and marrow walls block line of sight
        return terrain in [TerrainType.LIMESTONE, TerrainType.PILLAR, TerrainType.MARROW_WALL]

    def get_cosmic_value(self, y: int, x: int, player=None, game=None) -> Optional[int]:
        """
        Get cosmic value at the given coordinates.
        Returns None if no value is set or if the terrain is not furniture.
        The player parameter is used to check if the player can see the cosmic value.
        Only players with DELPHIC_APPRAISER units can see the values.
        """
        # Check if the position has furniture
        terrain = self.get_terrain_at(y, x)
        if terrain not in [TerrainType.FURNITURE, TerrainType.COAT_RACK,
                          TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
            return None

        # Check if player has DELPHIC_APPRAISER
        if player is None or game is None:
            return None

        # Check if the player has a DELPHIC_APPRAISER unit
        from boneglaive.utils.constants import UnitType
        has_appraiser = False
        for unit in game.units:
            if unit.player == player and unit.type == UnitType.DELPHIC_APPRAISER and unit.is_alive():
                has_appraiser = True
                break

        if not has_appraiser:
            return None

        # Generate value if not already set
        if (y, x) not in self.cosmic_values:
            import random
            self.cosmic_values[(y, x)] = random.randint(1, 9)

        # Return the cosmic value
        return self.cosmic_values.get((y, x))

    def set_cosmic_value(self, y: int, x: int, value: int) -> bool:
        """
        Set cosmic value at the given coordinates.
        Returns True if successful, False if the terrain is not furniture.
        """
        # Check if the position has furniture
        terrain = self.get_terrain_at(y, x)
        if terrain not in [TerrainType.FURNITURE, TerrainType.COAT_RACK,
                          TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]:
            return False

        # Set the cosmic value
        self.cosmic_values[(y, x)] = value
        return True

    def is_furniture(self, y: int, x: int) -> bool:
        """Check if a position has furniture."""
        terrain = self.get_terrain_at(y, x)
        return terrain in [TerrainType.FURNITURE, TerrainType.COAT_RACK,
                          TerrainType.OTTOMAN, TerrainType.CONSOLE, TerrainType.DEC_TABLE]

    def has_rails(self) -> bool:
        """Check if the map currently has any rail tiles."""
        for terrain in self.terrain.values():
            if terrain == TerrainType.RAIL:
                return True
        return False

    def generate_rail_network(self) -> None:
        """
        Generate a symmetrical rail network covering significant map area.
        Creates cross pattern from map center with diagonal branches.
        Rails don't pass through terrain or furniture.
        """
        center_y = self.height // 2
        center_x = self.width // 2
        
        # Create main cross pattern
        # Horizontal line (East-West)
        for x in range(self.width):
            if self._can_place_rail(center_y, x):
                self.set_terrain_at(center_y, x, TerrainType.RAIL)
        
        # Vertical line (North-South) 
        for y in range(self.height):
            if self._can_place_rail(y, center_x):
                self.set_terrain_at(y, center_x, TerrainType.RAIL)
        
        # Create diagonal branches at 4-tile intervals from center
        # These provide good vantage points without cluttering
        diagonal_positions = [
            # Main diagonals from center
            (center_y - 2, center_x - 2), (center_y - 2, center_x + 2),
            (center_y + 2, center_x - 2), (center_y + 2, center_x + 2),
            # Additional strategic positions
            (center_y - 1, center_x - 4), (center_y - 1, center_x + 4),
            (center_y + 1, center_x - 4), (center_y + 1, center_x + 4),
            # Corner approach rails (for map edges)
            (1, 2), (1, self.width - 3),
            (self.height - 2, 2), (self.height - 2, self.width - 3)
        ]
        
        # Add diagonal connection rails
        for y, x in diagonal_positions:
            if self._can_place_rail(y, x):
                self.set_terrain_at(y, x, TerrainType.RAIL)
        
        # Connect diagonal positions to main lines with short branch rails
        self._add_diagonal_connections(center_y, center_x)

    def _can_place_rail(self, y: int, x: int) -> bool:
        """Check if a rail can be placed at this position."""
        if not (0 <= y < self.height and 0 <= x < self.width):
            return False
        
        terrain = self.get_terrain_at(y, x)
        # Rails can be placed on empty, dust, or existing rail tiles
        # Cannot be placed on blocking terrain or furniture
        return terrain in [TerrainType.EMPTY, TerrainType.DUST, TerrainType.RAIL]

    def _add_diagonal_connections(self, center_y: int, center_x: int) -> None:
        """Add connecting rails between diagonal positions and main lines."""
        # Add short connection segments to make the network more connected
        # while keeping it clean and not overly intricate
        
        # Upper diagonal connections
        if self._can_place_rail(center_y - 1, center_x - 1):
            self.set_terrain_at(center_y - 1, center_x - 1, TerrainType.RAIL)
        if self._can_place_rail(center_y - 1, center_x + 1):
            self.set_terrain_at(center_y - 1, center_x + 1, TerrainType.RAIL)
        
        # Lower diagonal connections  
        if self._can_place_rail(center_y + 1, center_x - 1):
            self.set_terrain_at(center_y + 1, center_x - 1, TerrainType.RAIL)
        if self._can_place_rail(center_y + 1, center_x + 1):
            self.set_terrain_at(center_y + 1, center_x + 1, TerrainType.RAIL)

    def get_rail_positions(self) -> List[Tuple[int, int]]:
        """Get all positions that have rail tiles."""
        rail_positions = []
        for (y, x), terrain in self.terrain.items():
            if terrain == TerrainType.RAIL:
                rail_positions.append((y, x))
        return rail_positions


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
        
        # Add strategically placed furniture
        
        # Entry vestibule furniture
        self.set_terrain_at(1, 1, TerrainType.FURNITURE)   # Corner plant (entrance decor)
        self.set_terrain_at(1, 18, TerrainType.FURNITURE)  # Corner plant (entrance decor)
        
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
        
        # Logical furniture arrangement for a foyer
        
        # Coat racks near entrance
        self.set_terrain_at(0, 4, TerrainType.COAT_RACK)  # Left coat rack for visitors
        self.set_terrain_at(0, 15, TerrainType.COAT_RACK) # Right coat rack for visitors
        
        # Reception/check-in area
        self.set_terrain_at(2, 4, TerrainType.CONSOLE)    # Reception desk
        self.set_terrain_at(2, 5, TerrainType.FURNITURE)  # Reception chair
        
        # Main waiting area (centered in open space)
        self.set_terrain_at(4, 15, TerrainType.OTTOMAN)   # Right ottoman
        self.set_terrain_at(5, 15, TerrainType.OTTOMAN)   # Right ottoman extension
        self.set_terrain_at(4, 4, TerrainType.OTTOMAN)    # Left ottoman
        self.set_terrain_at(5, 4, TerrainType.OTTOMAN)    # Left ottoman extension
        
        # Center coffee/magazine tables
        self.set_terrain_at(4, 3, TerrainType.DEC_TABLE)  # Side table by ottoman
        self.set_terrain_at(4, 16, TerrainType.DEC_TABLE) # Side table by ottoman
        
        # Lower seating area (near second pillar)
        self.set_terrain_at(8, 4, TerrainType.OTTOMAN)    # Lower lobby ottoman
        self.set_terrain_at(8, 15, TerrainType.OTTOMAN)   # Lower lobby ottoman opposite
        
        # Decorative elements
        self.set_terrain_at(6, 5, TerrainType.FURNITURE)  # Plant between seating areas
        self.set_terrain_at(6, 14, TerrainType.FURNITURE) # Plant between seating areas
        
        # Light limestone dustings (windswept patterns)
        # This is a partial list - approximately 50% of tiles will have dust
        dust_patterns = [
            # Top row dust
            (0, 0), (0, 1), (0, 3), (0, 4), (0, 6), (0, 7), (0, 8), (0, 9), (0, 11), (0, 12), (0, 13), (0, 15), (0, 16), (0, 18), (0, 19),
            
            # Second row dust
            (1, 0), (1, 1), (1, 4), (1, 5), (1, 6), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 19),
            
            # Third row dust
            (2, 0), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 10), (2, 11), (2, 12), (2, 13), (2, 15), (2, 16), (2, 17), (2, 19),
            
            # Fourth row dust
            (3, 0), (3, 1), (3, 4), (3, 5), (3, 6), (3, 10), (3, 11), (3, 12), (3, 14), (3, 15), (3, 17), (3, 18), (3, 19),
            
            # Fifth row dust
            (4, 1), (4, 2), (4, 4), (4, 5), (4, 6), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 17), (4, 18), (4, 19),
            
            # Sixth row dust
            (5, 0), (5, 1), (5, 3), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 11), (5, 12), (5, 14), (5, 15), (5, 16), (5, 17), (5, 18), (5, 19),
            
            # Seventh row dust
            (6, 0), (6, 1), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 11), (6, 12), (6, 13), (6, 14), (6, 17), (6, 18),
            
            # Eighth row dust
            (7, 0), (7, 1), (7, 2), (7, 4), (7, 5), (7, 6), (7, 12), (7, 13), (7, 14), (7, 15), (7, 17), (7, 18), (7, 19),
            
            # Ninth row dust
            (8, 0), (8, 1), (8, 2), (8, 4), (8, 5), (8, 6), (8, 12), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19),
            
            # Bottom row dust
            (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 12), (9, 14), (9, 16), (9, 17), (9, 18), (9, 19)
        ]
        
        for y, x in dust_patterns:
            # Only set dust if the tile is empty (not already a pillar, furniture, etc.)
            if self.get_terrain_at(y, x) == TerrainType.EMPTY:
                self.set_terrain_at(y, x, TerrainType.DUST)

        # Cosmic values will be assigned when needed during gameplay


class NewLimeFoyerMap(GameMap):
    """The New Lime Foyer map featuring a central circular pit arena with strategic furniture placement."""
    
    def __init__(self):
        super().__init__()
        self.name = "The Lime Foyer Arena"
        self.generate_map()
    
    def generate_map(self) -> None:
        """Generate the New Lime Foyer map with central arena pit."""
        # Reset to empty first
        self.reset_to_empty()
        
        # Central circular pit (7x7 with rounded corners)
        pit_wall = [
            # Top row
            (1, 8), (1, 9), (1, 10), (1, 11),
            # Left side
            (2, 7), (3, 6), (4, 6), (5, 6), (6, 7),
            # Right side
            (2, 12), (3, 13), (4, 13), (5, 13), (6, 12),
            # Bottom row
            (7, 8), (7, 9), (7, 10), (7, 11)
        ]
        
        for y, x in pit_wall:
            self.set_terrain_at(y, x, TerrainType.LIMESTONE)
        
        # --- Strategic furniture placement ---
        
        # Pattern 1: Symmetrical furniture in the four corners (good for Divine Depreciation)
        # Top-left corner
        self.set_terrain_at(0, 0, TerrainType.COAT_RACK)
        self.set_terrain_at(0, 3, TerrainType.CONSOLE)
        self.set_terrain_at(2, 0, TerrainType.DEC_TABLE)
        
        # Top-right corner
        self.set_terrain_at(0, 19, TerrainType.COAT_RACK)
        self.set_terrain_at(0, 16, TerrainType.CONSOLE)
        self.set_terrain_at(2, 19, TerrainType.DEC_TABLE)
        
        # Bottom-left corner
        self.set_terrain_at(9, 0, TerrainType.OTTOMAN)
        self.set_terrain_at(9, 3, TerrainType.CONSOLE)
        self.set_terrain_at(7, 0, TerrainType.DEC_TABLE)
        
        # Bottom-right corner
        self.set_terrain_at(9, 19, TerrainType.OTTOMAN)
        self.set_terrain_at(9, 16, TerrainType.CONSOLE)
        self.set_terrain_at(7, 19, TerrainType.DEC_TABLE)
        
        # Pattern 2: Furniture clusters around the pit (optimal for Market Futures teleportation)
        # North cluster
        self.set_terrain_at(0, 9, TerrainType.OTTOMAN)
        self.set_terrain_at(0, 10, TerrainType.CONSOLE)
        
        # East cluster
        self.set_terrain_at(4, 17, TerrainType.OTTOMAN)
        self.set_terrain_at(5, 17, TerrainType.DEC_TABLE)
        
        # West cluster
        self.set_terrain_at(4, 2, TerrainType.OTTOMAN)
        self.set_terrain_at(5, 2, TerrainType.DEC_TABLE)
        
        # South cluster
        self.set_terrain_at(9, 9, TerrainType.OTTOMAN)
        self.set_terrain_at(9, 10, TerrainType.CONSOLE)
        
        # Pattern 3: Inner ring furniture just outside the pit (for Auction Curse positioning)
        self.set_terrain_at(3, 4, TerrainType.FURNITURE)
        self.set_terrain_at(3, 15, TerrainType.FURNITURE)
        self.set_terrain_at(6, 4, TerrainType.FURNITURE)
        self.set_terrain_at(6, 15, TerrainType.FURNITURE)
        
        # Pattern 4: Central pit furniture pieces (few but valuable tactical positions)
        self.set_terrain_at(4, 8, TerrainType.OTTOMAN)
        self.set_terrain_at(4, 11, TerrainType.OTTOMAN)
        
        # Light limestone dustings (windswept patterns)
        dust_patterns = [
            # Top half dust pattern (roughly 40% coverage)
            (0, 1), (0, 2), (0, 4), (0, 6), (0, 7), (0, 8), (0, 11), (0, 12), (0, 13), (0, 15), (0, 17), (0, 18),
            (1, 0), (1, 1), (1, 3), (1, 5), (1, 6), (1, 7), (1, 12), (1, 13), (1, 14), (1, 16), (1, 18), (1, 19),
            (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 8), (2, 9), (2, 10), (2, 11), (2, 13), (2, 14), (2, 15), (2, 17), (2, 18),
            (3, 0), (3, 2), (3, 3), (3, 5), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 14), (3, 16), (3, 17), (3, 19),
            
            # Bottom half dust pattern (matching pattern to top, rotated)
            (6, 0), (6, 2), (6, 3), (6, 5), (6, 8), (6, 9), (6, 10), (6, 11), (6, 13), (6, 14), (6, 16), (6, 17), (6, 19),
            (7, 1), (7, 2), (7, 4), (7, 5), (7, 6), (7, 7), (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 18),
            (8, 0), (8, 1), (8, 3), (8, 4), (8, 6), (8, 7), (8, 12), (8, 13), (8, 15), (8, 16), (8, 18), (8, 19),
            (9, 1), (9, 2), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (9, 11), (9, 12), (9, 13), (9, 15), (9, 17), (9, 18)
        ]
        
        for y, x in dust_patterns:
            # Only set dust if the tile is empty
            if self.get_terrain_at(y, x) == TerrainType.EMPTY:
                self.set_terrain_at(y, x, TerrainType.DUST)


class MapFactory:
    """Factory class for creating different maps."""
    
    @staticmethod
    def create_map(map_name: str) -> GameMap:
        """Create a map based on the given name."""
        if map_name.lower() == "lime_foyer":
            return LimeFoyerMap()
        elif map_name.lower() == "lime_foyer_arena":
            return NewLimeFoyerMap()
        else:
            # Default to empty map
            return GameMap()