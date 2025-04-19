#!/usr/bin/env python3
from enum import Enum

# Game constants
WIDTH = 20
HEIGHT = 10
MAX_UNITS = 3  # Maximum units per player

class UnitType(Enum):
    WARRIOR = 0
    ARCHER = 1
    MAGE = 2

# Unit stats: (hp, attack, defense, move_range, attack_range)
UNIT_STATS = {
    UnitType.WARRIOR: (20, 8, 5, 2, 1),
    UnitType.ARCHER: (15, 7, 2, 2, 3),
    UnitType.MAGE: (12, 10, 1, 1, 2)
}

UNIT_SYMBOLS = {
    UnitType.WARRIOR: 'W',
    UnitType.ARCHER: 'A',
    UnitType.MAGE: 'M'
}

# Attack visual effects
ATTACK_EFFECTS = {
    UnitType.WARRIOR: "⚔️",  # Sword (melee)
    UnitType.ARCHER: "→",    # Arrow (ranged)
    UnitType.MAGE: "*"       # Magic star (ranged)
}