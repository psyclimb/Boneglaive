#!/usr/bin/env python3
from enum import Enum
from typing import Dict

# Game constants
WIDTH = 20
HEIGHT = 10
MAX_UNITS = 3  # Maximum units per player
CRITICAL_HEALTH_PERCENT = 0.3  # Percentage of max HP considered "critical"

# Experience and leveling constants
MAX_LEVEL = 5  # Maximum level a unit can reach
XP_KILL_REWARD = 0  # Base XP for killing an enemy (temporarily set to 0 for testing)
XP_DAMAGE_FACTOR = 0  # XP per point of damage dealt (temporarily set to 0 for testing)

# XP required for each level
XP_PER_LEVEL = {
    1: 0,     # Starting level
    2: 20,    # XP needed for level 2
    3: 50,    # XP needed for level 3
    4: 100,   # XP needed for level 4
    5: 200    # XP needed for level 5
}

class UnitType(Enum):
    GLAIVEMAN = 0
    ARCHER = 1
    MAGE = 2

# Unit stats: (hp, attack, defense, move_range, attack_range)
UNIT_STATS = {
    UnitType.GLAIVEMAN: (20, 5, 1, 2, 1),
    UnitType.ARCHER: (15, 5, 2, 2, 3),
    UnitType.MAGE: (12, 6, 1, 1, 2)
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

# Greek alphabet for unit identification
GREEK_ALPHABET = [
    'α',  # alpha
    'β',  # beta
    'γ',  # gamma
    'δ',  # delta
    'ε',  # epsilon
    'ζ',  # zeta
    'η',  # eta
    'θ',  # theta
    'ι',  # iota
    'κ',  # kappa
    'λ',  # lambda
    'μ',  # mu
    'ν',  # nu
    'ξ',  # xi
    'ο',  # omicron
    'π',  # pi
    'ρ',  # rho
    'σ',  # sigma
    'τ',  # tau
    'υ',  # upsilon
    'φ',  # phi
    'χ',  # chi
    'ψ',  # psi
    'ω'   # omega
]