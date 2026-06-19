#!/usr/bin/env python3
"""Game constants, unit types, stats, and symbols."""
from enum import Enum
from typing import Dict, NamedTuple

# Game constants
WIDTH = 20
HEIGHT = 10
MAX_UNITS = 3  # Maximum units per player
RESPAWN_TIMER = 3  # Turns until dead unit can respawn
UPGRADE_POINT_THRESHOLDS = [2, 4, 6]  # GP thresholds that award upgrade points
INVULNERABLE_PRT = 999  # PRT value for effectively invulnerable units (Heinous Vapor, Topiary)
CRITICAL_HEALTH_PERCENT = 0.3  # Percentage of max HP considered "critical"

class UnitType(Enum):
    GLAIVEMAN = 0
    MANDIBLE_FOREMAN = 3  # This stays as MANDIBLE_FOREMAN in the enum (no spaces allowed)
    GRAYMAN = 4  # The Immutable Anomaly
    MARROW_CONDENSER = 5  # The skeletal bone manipulator (displayed as MARROW CONDENSER)
    FOWL_CONTRIVANCE = 6  # The synchronized bird flock formation
    GAS_MACHINIST = 7  # The vapor-controlling technician
    HEINOUS_VAPOR = 8  # Vapor entity controlled by GAS_MACHINIST
    DELPHIC_APPRAISER = 9  # The furniture evaluator with astral value perception
    INTERFERER = 10  # The telecommunications engineer turned assassin
    DERELICTIONIST = 11  # The psychological abandonment therapist
    POTPOURRIST = 12  # The tank with potpourri-enhanced healing
    LANDSCAPER = 13  # The four-armed terrain manipulator with acoustic levitation

class UnitStats(NamedTuple):
    """Base stats for a unit type. Tuple order preserved for unpacking compatibility."""
    hp: int
    attack: int
    defense: int
    move_range: int
    attack_range: int

UNIT_STATS = {
    UnitType.GLAIVEMAN: UnitStats(22, 5, 1, 3, 2),
    UnitType.MANDIBLE_FOREMAN: UnitStats(22, 3, 1, 3, 1),
    UnitType.GRAYMAN: UnitStats(18, 4, 0, 4, 5),
    UnitType.MARROW_CONDENSER: UnitStats(22, 4, 2, 3, 1),
    UnitType.FOWL_CONTRIVANCE: UnitStats(18, 4, 0, 3, 3),
    UnitType.GAS_MACHINIST: UnitStats(20, 4, 1, 3, 2),
    UnitType.HEINOUS_VAPOR: UnitStats(1, 0, 0, 4, 1),
    UnitType.DELPHIC_APPRAISER: UnitStats(20, 3, 0, 4, 2),
    UnitType.INTERFERER: UnitStats(18, 4, 0, 4, 1),
    UnitType.DERELICTIONIST: UnitStats(18, 0, 0, 4, 1),
    UnitType.POTPOURRIST: UnitStats(24, 5, 0, 3, 1),
    UnitType.LANDSCAPER: UnitStats(20, 1, 1, 2, 1)
}

UNIT_SYMBOLS = {
    UnitType.GLAIVEMAN: 'G',
    UnitType.MANDIBLE_FOREMAN: 'F',
    UnitType.GRAYMAN: 'Ψ',  # Greek psi for Psi/anomalous nature
    UnitType.MARROW_CONDENSER: 'C',  # C for Condenser
    UnitType.FOWL_CONTRIVANCE: 'T',  # T for Turret/artillery (matches help page)
    UnitType.GAS_MACHINIST: 'M',  # M for Machinist
    UnitType.HEINOUS_VAPOR: 'V',  # Generic vapor symbol, actual symbols set in skills
    UnitType.DELPHIC_APPRAISER: 'A',  # A for Appraiser
    UnitType.INTERFERER: 'R',  # R for Radioactive interference
    UnitType.DERELICTIONIST: 'D',  # D for DERELICTIONIST
    UnitType.POTPOURRIST: 'P',  # P for POTPOURRIST
    UnitType.LANDSCAPER: 'L'  # L for LANDSCAPER
}

# GP (Game Points) System
# Units that award GP when killed (main units only, no summons/doppelgangers)
GP_ELIGIBLE_UNITS = {
    UnitType.GLAIVEMAN,
    UnitType.MANDIBLE_FOREMAN,
    UnitType.POTPOURRIST,
    UnitType.GRAYMAN,
    UnitType.INTERFERER,
    UnitType.DELPHIC_APPRAISER,
    UnitType.MARROW_CONDENSER,
    UnitType.DERELICTIONIST,
    UnitType.FOWL_CONTRIVANCE,
    UnitType.GAS_MACHINIST,
    UnitType.LANDSCAPER
}

# Greek alphabet for unit identification
UNIT_ID_ALPHABET = [
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

# Unit display names for UI
UNIT_DISPLAY_NAMES = {
    UnitType.GLAIVEMAN: 'GLAIVEMAN',
    UnitType.MANDIBLE_FOREMAN: 'MANDIBLE FOREMAN',
    UnitType.GRAYMAN: 'GRAYMAN',
    UnitType.MARROW_CONDENSER: 'MARROW CONDENSER',
    UnitType.FOWL_CONTRIVANCE: 'FOWL CONTRIVANCE',
    UnitType.GAS_MACHINIST: 'GAS MACHINIST',
    UnitType.HEINOUS_VAPOR: 'HEINOUS VAPOR',
    UnitType.DELPHIC_APPRAISER: 'DELPHIC APPRAISER',
    UnitType.INTERFERER: 'INTERFERER',
    UnitType.DERELICTIONIST: 'DERELICTIONIST',
    UnitType.POTPOURRIST: 'POTPOURRIST',
    UnitType.LANDSCAPER: 'LANDSCAPER'
}
