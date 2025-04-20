#!/usr/bin/env python3
from enum import Enum

# Game constants
WIDTH = 20
HEIGHT = 10
MAX_UNITS = 3  # Maximum units per player
CRITICAL_HEALTH_PERCENT = 0.3  # Percentage of max HP considered "critical"

class UnitType(Enum):
    GLAIVEMAN = 0
    ARCHER = 1
    MAGE = 2

# Unit stats: (hp, attack, defense, move_range, attack_range)
UNIT_STATS = {
    UnitType.GLAIVEMAN: (20, 8, 5, 2, 1),
    UnitType.ARCHER: (15, 7, 2, 2, 3),
    UnitType.MAGE: (12, 10, 1, 1, 2)
}

UNIT_SYMBOLS = {
    UnitType.GLAIVEMAN: 'G',
    UnitType.ARCHER: 'A',
    UnitType.MAGE: 'M'
}

# Attack visual effects
ATTACK_EFFECTS = {
    UnitType.GLAIVEMAN: "⚔️",  # Glaive (melee)
    UnitType.ARCHER: "→",      # Arrow (ranged)
    UnitType.MAGE: "*"         # Magic star (ranged)
}