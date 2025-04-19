#!/usr/bin/env python3
"""
Coordinate system utilities for handling game coordinates.
Provides translation between logical game coordinates and display coordinates.
"""

from dataclasses import dataclass
from typing import List, Tuple, Union

@dataclass
class Position:
    """Represents a position in the game grid."""
    y: int
    x: int
    
    def __add__(self, other: Union['Position', Tuple[int, int]]) -> 'Position':
        """Add two positions or a position and a tuple."""
        if isinstance(other, Position):
            return Position(self.y + other.y, self.x + other.x)
        elif isinstance(other, tuple) and len(other) == 2:
            return Position(self.y + other[0], self.x + other[1])
        else:
            raise TypeError("Can only add Position or tuple of length 2")
    
    def __sub__(self, other: Union['Position', Tuple[int, int]]) -> 'Position':
        """Subtract two positions or a position and a tuple."""
        if isinstance(other, Position):
            return Position(self.y - other.y, self.x - other.x)
        elif isinstance(other, tuple) and len(other) == 2:
            return Position(self.y - other[0], self.x - other[1])
        else:
            raise TypeError("Can only subtract Position or tuple of length 2")
    
    def __eq__(self, other: object) -> bool:
        """Check if two positions are equal."""
        if not isinstance(other, Position):
            return False
        return self.y == other.y and self.x == other.x
    
    def __hash__(self) -> int:
        """Hash function for using Position as a dictionary key."""
        return hash((self.y, self.x))
    
    def as_tuple(self) -> Tuple[int, int]:
        """Return position as a tuple (y, x)."""
        return (self.y, self.x)
    
    def distance_to(self, other: Union['Position', Tuple[int, int]]) -> int:
        """Calculate Manhattan distance to another position."""
        if isinstance(other, Position):
            return abs(self.y - other.y) + abs(self.x - other.x)
        elif isinstance(other, tuple) and len(other) == 2:
            return abs(self.y - other[0]) + abs(self.x - other[1])
        else:
            raise TypeError("Can only calculate distance to Position or tuple of length 2")
    
    def is_adjacent(self, other: Union['Position', Tuple[int, int]]) -> bool:
        """Check if position is adjacent (including diagonals)."""
        return self.distance_to(other) <= 2
    
    def is_in_bounds(self, height: int, width: int) -> bool:
        """Check if position is within bounds."""
        return 0 <= self.y < height and 0 <= self.x < width

def get_positions_in_range(center: Position, range_value: int, 
                          height: int, width: int) -> List[Position]:
    """Get all positions within a certain range of a center position."""
    positions = []
    
    for y in range(max(0, center.y - range_value), min(height, center.y + range_value + 1)):
        for x in range(max(0, center.x - range_value), min(width, center.x + range_value + 1)):
            pos = Position(y, x)
            if pos.distance_to(center) <= range_value:
                positions.append(pos)
    
    return positions

def get_line(start: Position, end: Position) -> List[Position]:
    """Get a list of positions forming a line from start to end."""
    positions = []
    
    # Use Bresenham's line algorithm
    y0, x0 = start.y, start.x
    y1, x1 = end.y, end.x
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        positions.append(Position(y0, x0))
        
        if x0 == x1 and y0 == y1:
            break
            
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    
    return positions