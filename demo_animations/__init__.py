"""
Demo Animations Package
Modular animation system for Boneglaive unit skill demonstrations.
"""

from .core import (
    Particle,
    ParticleEmitter,
    AnimatedUnit,
    FloatingText,
    DebrisParticle
)

from .glaiveman import (
    SpinningGlaiveProjectile,
    LightningBolt,
    CrossBeam
)

from .mandible_foreman import (
    JawClamp,
    ViseroyTrap,
    ViseroyRelease,
    SiteInspectionBuff,
    SiteInspectionScan,
    ExpediteRush,
    JawlineNetwork
)

from .potpourrist import (
    PedestalStrike,
    InfuseEffect,
    DemiluneSwing,
    LunacyEffect,
    GraniteGeasEffect,
    GeasBreakHeal,
    MelangeEminence
)

__all__ = [
    # Core
    'Particle',
    'ParticleEmitter',
    'AnimatedUnit',
    'FloatingText',
    'DebrisParticle',
    # Glaiveman
    'SpinningGlaiveProjectile',
    'LightningBolt',
    'CrossBeam',
    # Mandible Foreman
    'JawClamp',
    'ViseroyTrap',
    'ViseroyRelease',
    'SiteInspectionBuff',
    'SiteInspectionScan',
    'ExpediteRush',
    'JawlineNetwork',
    # Potpourrist
    'PedestalStrike',
    'InfuseEffect',
    'DemiluneSwing',
    'LunacyEffect',
    'GraniteGeasEffect',
    'GeasBreakHeal',
    'MelangeEminence',
]
