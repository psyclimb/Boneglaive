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
    MANDIBLE_FOREMAN = 3  # This stays as MANDIBLE_FOREMAN in the enum (no spaces allowed)
    GRAYMAN = 4  # The Immutable Anomaly
    MARROW_CONDENSER = 5  # The skeletal bone manipulator (displayed as MARROW CONDENSER)
    FOWL_CONTRIVANCE = 6  # The synchronized bird flock formation
    GAS_MACHINIST = 7  # The vapor-controlling technician
    HEINOUS_VAPOR = 8  # Vapor entity controlled by GAS_MACHINIST
    DELPHIC_APPRAISER = 9  # The furniture evaluator with cosmic value perception
    INTERFERER = 10  # The telecommunications engineer turned assassin

# Unit stats: (hp, attack, defense, move_range, attack_range)
UNIT_STATS = {
    UnitType.GLAIVEMAN: (22, 4, 1, 2, 2),
    UnitType.ARCHER: (15, 5, 2, 2, 3),
    UnitType.MAGE: (12, 6, 1, 1, 2),
    UnitType.MANDIBLE_FOREMAN: (22, 3, 1, 2, 1),
    UnitType.GRAYMAN: (18, 3, 0, 2, 5),
    UnitType.MARROW_CONDENSER: (20, 4, 2, 3, 1),
    UnitType.FOWL_CONTRIVANCE: (18, 5, 0, 4, 2),
    UnitType.GAS_MACHINIST: (18, 4, 1, 3, 1),
    UnitType.HEINOUS_VAPOR: (10, 0, 0, 3, 1),
    UnitType.DELPHIC_APPRAISER: (20, 4, 0, 3, 1),
    UnitType.INTERFERER: (18, 4, 0, 2, 1)
}

UNIT_SYMBOLS = {
    UnitType.GLAIVEMAN: 'G',
    UnitType.ARCHER: 'A',
    UnitType.MAGE: 'M',
    UnitType.MANDIBLE_FOREMAN: 'F',
    UnitType.GRAYMAN: 'Ψ',  # Greek psi symbol represents the anomalous nature
    UnitType.MARROW_CONDENSER: 'C',  # C for Condenser
    UnitType.FOWL_CONTRIVANCE: '^',  # Birds in flight
    UnitType.GAS_MACHINIST: 'M',  # M for Machinist
    UnitType.HEINOUS_VAPOR: 'V',  # Generic vapor symbol, actual symbols set in skills
    UnitType.DELPHIC_APPRAISER: 'A',  # A for Appraiser
    UnitType.INTERFERER: 'R'  # R for Radioactive interference
}

# Attack visual effects
ATTACK_EFFECTS = {
    UnitType.GLAIVEMAN: "/",  # Glaive (melee)
    UnitType.ARCHER: "→",      # Arrow (ranged)
    UnitType.MAGE: "*",        # Magic star (ranged)
    UnitType.GRAYMAN: "≈",     # Reality distortion (ranged)
    UnitType.MANDIBLE_FOREMAN: "Ξ",  # Mandible jaws (melee)
    UnitType.MARROW_CONDENSER: "Ø",  # Bone (melee)
    UnitType.FOWL_CONTRIVANCE: "Λ",   # Bird dive attack (ranged)
    UnitType.GAS_MACHINIST: "o",   # Gas bubble (melee)
    UnitType.HEINOUS_VAPOR: "~",    # Vapor effect (area)
    UnitType.DELPHIC_APPRAISER: "$",  # Currency symbol (evaluation)
    UnitType.INTERFERER: "x"  # Plutonium carabiner cross (melee)
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

# Status effect symbols
STATUS_EFFECT_SYMBOLS = {
    'MIRED': '≈',             # Movement reduction from upgraded marrow dike
    'RADIATION_SICKNESS': 'r', # Radiation damage over time
    'NEURAL_SHUNT': '?',      # Random action control
    'CARRIER_RAVE': 'φ',      # Phased/untargetable state
}
