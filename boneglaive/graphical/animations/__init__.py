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
    GraymanEchoDeathExplosionAnimation,
)

from .interferer import (
    NeutronIlluminantCardinal,
    NeutronIlluminantDiagonal,
    NeuralShuntAnimation,
    ScalarNodeTriggerAnimation,
    KarrierRavePhaseOut,
    KarrierRaveTripleStrike,
)

from .delphic_appraiser import (
    DivineDrepreciationAnimation,
    AuctionCurseAnimation,
    MarketFuturesAnimation,
)

from .marrow_condenser import (
    OssifyAnimation,
    BoneTitheAnimation,
    MarrowDikeAnimation,
    MarrowDikeWallDespawnAnimation,
)

from .derelictionist import (
    PartitionAnimation,
    PartitionHitAnimation,
    PartitionDissociationAnimation,
    DerelictedApplicationAnimation,
    DerelictionistDefectTeleportAnimation,
    VagalRunAnimation,
    VagalRunAbreactionAnimation,
)

from .fowl_contrivance import (
    ParabolAnimation,
    FragcrestAnimation,
    GaussianDuskChargeAnimation,
    GaussianDuskFireAnimation,
    RailGenesisDeathExplosionAnimation,
)

from .gas_machinist import (
    VaporSpawnAnimation,
    DivergeAnimation,
    VaporAOETickAnimation,
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
    'GraymanEchoDeathExplosionAnimation',
    # Interferer
    'NeutronIlluminantCardinal',
    'NeutronIlluminantDiagonal',
    'NeuralShuntAnimation',
    'ScalarNodeTriggerAnimation',
    'KarrierRavePhaseOut',
    'KarrierRaveTripleStrike',
    # Delphic Appraiser
    'DivineDrepreciationAnimation',
    'AuctionCurseAnimation',
    'MarketFuturesAnimation',
    # Marrow Condenser
    'OssifyAnimation',
    'BoneTitheAnimation',
    'MarrowDikeAnimation',
    'MarrowDikeWallDespawnAnimation',
    # Derelictionist
    'PartitionAnimation',
    'PartitionHitAnimation',
    'PartitionDissociationAnimation',
    'DerelictedApplicationAnimation',
    'DerelictionistDefectTeleportAnimation',
    'VagalRunAnimation',
    'VagalRunAbreactionAnimation',
    # Fowl Contrivance
    'ParabolAnimation',
    'FragcrestAnimation',
    'GaussianDuskChargeAnimation',
    'GaussianDuskFireAnimation',
    'RailGenesisDeathExplosionAnimation',
    # Gas Machinist
    'VaporSpawnAnimation',
    'DivergeAnimation',
    'VaporAOETickAnimation',
    # Factory
    'AnimationFactory',
]
