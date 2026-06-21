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
BOMB_MAX_STACKS = 4  # ORDNANCE GRAFT: max bombs on one target
BOMB_LIFESPAN = 6  # ORDNANCE GRAFT: turns a bomb lingers before falling off (refreshed on re-graft)
ORDNANCE_DRONE_REGEN = 4  # ORDNANCE GRAFT: turns to regenerate a destroyed drone
ORDNANCE_DRONE_LEASH = 3  # ORDNANCE GRAFT: max tiles the drone may stray from its owner

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
    ORDNANCE_GRAFT = 14  # The gunner who grafts %HP bombs and touches them off
    ORDNANCE_DRONE = 15  # ORDNANCE_GRAFT's leashed quadcopter summon

class UnitStats(NamedTuple):
    """Base stats for a unit type. Tuple order preserved for unpacking compatibility."""
    hp: int
    attack: int
    defense: int
    move_range: int
    attack_range: int


class UnitDescriptor(NamedTuple):
    """Single source of truth for a unit's identity: name, symbol, stats, and flags.

    Skill wiring lives in skills/registry.py (it needs skill-class imports that
    must not reach down into this low-level module). Everything else about a
    unit's identity is defined here; the legacy lookup tables below are derived
    views over UNIT_DESCRIPTORS, so adding a unit means adding one entry here.
    """
    unit_type: 'UnitType'
    display_name: str
    symbol: str
    stats: UnitStats
    recruitable: bool = True   # appears in the setup-phase recruitment roster
    awards_gp: bool = True     # killing it awards a Game Point (False for summons)


# Ordered identity table. Order is the recruitment/selection order.
UNIT_DESCRIPTORS = (
    UnitDescriptor(UnitType.GLAIVEMAN, 'GLAIVEMAN', 'G', UnitStats(22, 5, 1, 3, 2)),
    UnitDescriptor(UnitType.MANDIBLE_FOREMAN, 'MANDIBLE FOREMAN', 'F', UnitStats(22, 3, 1, 3, 1)),
    UnitDescriptor(UnitType.GRAYMAN, 'GRAYMAN', 'Ψ', UnitStats(18, 4, 0, 4, 5)),
    UnitDescriptor(UnitType.MARROW_CONDENSER, 'MARROW CONDENSER', 'C', UnitStats(22, 4, 2, 3, 1)),
    UnitDescriptor(UnitType.FOWL_CONTRIVANCE, 'FOWL CONTRIVANCE', 'T', UnitStats(18, 4, 0, 3, 3)),
    UnitDescriptor(UnitType.GAS_MACHINIST, 'GAS MACHINIST', 'M', UnitStats(20, 4, 1, 3, 2)),
    UnitDescriptor(UnitType.DELPHIC_APPRAISER, 'DELPHIC APPRAISER', 'A', UnitStats(20, 3, 0, 4, 2)),
    UnitDescriptor(UnitType.INTERFERER, 'INTERFERER', 'R', UnitStats(18, 4, 0, 4, 1)),
    UnitDescriptor(UnitType.DERELICTIONIST, 'DERELICTIONIST', 'D', UnitStats(18, 0, 0, 4, 1)),
    UnitDescriptor(UnitType.POTPOURRIST, 'POTPOURRIST', 'P', UnitStats(24, 5, 0, 3, 1)),
    UnitDescriptor(UnitType.LANDSCAPER, 'LANDSCAPER', 'L', UnitStats(20, 1, 1, 2, 1)),
    UnitDescriptor(UnitType.ORDNANCE_GRAFT, 'ORDNANCE GRAFT', 'Ø', UnitStats(20, 4, 0, 3, 2)),
    # HEINOUS_VAPOR is a GAS_MACHINIST summon: not recruitable, awards no GP.
    UnitDescriptor(UnitType.HEINOUS_VAPOR, 'HEINOUS VAPOR', 'V', UnitStats(1, 0, 0, 4, 1),
                   recruitable=False, awards_gp=False),
    # ORDNANCE_DRONE is an ORDNANCE_GRAFT summon: not recruitable, awards no GP.
    UnitDescriptor(UnitType.ORDNANCE_DRONE, 'ORDNANCE DRONE', 'q', UnitStats(6, 3, 2, 4, 2),
                   recruitable=False, awards_gp=False),
)

DESCRIPTORS_BY_TYPE = {d.unit_type: d for d in UNIT_DESCRIPTORS}

# Derived views — kept as the historical names/shapes so existing readers are
# unchanged. Do not edit these directly; edit UNIT_DESCRIPTORS above.
UNIT_STATS = {d.unit_type: d.stats for d in UNIT_DESCRIPTORS}
UNIT_SYMBOLS = {d.unit_type: d.symbol for d in UNIT_DESCRIPTORS}
GP_ELIGIBLE_UNITS = {d.unit_type for d in UNIT_DESCRIPTORS if d.awards_gp}

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

# Unit display names for UI (derived view over UNIT_DESCRIPTORS)
UNIT_DISPLAY_NAMES = {d.unit_type: d.display_name for d in UNIT_DESCRIPTORS}
