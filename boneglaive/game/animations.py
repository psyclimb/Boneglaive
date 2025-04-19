#!/usr/bin/env python3
import curses
import time
from boneglaive.utils.constants import UnitType, ATTACK_EFFECTS, UNIT_SYMBOLS

def get_line(y0, x0, y1, x1):
    """Get points in a line from (y0,x0) to (y1,x1) using Bresenham's algorithm"""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        points.append((y0, x0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    
    return points