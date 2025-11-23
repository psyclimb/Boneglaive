"""
Demo Animations Package
Modular animation system for Boneglaive unit skill demonstrations.
"""

from .core import (
    Particle,
    ParticleEmitter,
    AnimatedUnit,
    FloatingText,
    DebrisParticle,
    BasicMeleeAttackAnimation,
    StatusIconFlash
)

from .glaiveman import (
    SpinningGlaiveProjectile,
    LightningBolt,
    CrossBeam,
    AutoclaveAnimation,
    PryImpactAnimation,
    VaultAnimationController
)

from .mandible_foreman import (
    JawClamp,
    JawRelease,
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

from .grayman import (
    DeltaConfigAnimation,
    GraeExchangeAnimation,
    EstrangeBeam,
)

from .interferer import (
    NeutronIlluminantCardinal,
    NeutronIlluminantDiagonal,
    NeuralShuntAnimation,
    ScalarNodeTriggerAnimation,
    KarrierRavePhaseOut,
    KarrierRaveTripleStrike,
)

from .animation_factory import AnimationFactory

__all__ = [
    # Core
    'Particle',
    'ParticleEmitter',
    'AnimatedUnit',
    'FloatingText',
    'DebrisParticle',
    'BasicMeleeAttackAnimation',
    'StatusIconFlash',
    # Glaiveman
    'SpinningGlaiveProjectile',
    'LightningBolt',
    'CrossBeam',
    'AutoclaveAnimation',
    'PryImpactAnimation',
    'VaultAnimationController',
    # Mandible Foreman
    'JawClamp',
    'JawRelease',
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
    # Grayman
    'DeltaConfigAnimation',
    'GraeExchangeAnimation',
    'EstrangeBeam',
    # Interferer
    'NeutronIlluminantCardinal',
    'NeutronIlluminantDiagonal',
    'NeuralShuntAnimation',
    'ScalarNodeTriggerAnimation',
    'KarrierRavePhaseOut',
    'KarrierRaveTripleStrike',
    # Factory
    'AnimationFactory',
]
