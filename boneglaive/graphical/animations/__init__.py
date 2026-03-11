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

from .core_animations import (
    RespawnAnimation,
)

from .glaiveman import (
    SpinningGlaiveProjectile,
    LightningBolt,
    CrossBeam,
    AutoclaveAnimation,
    PryImpactAnimation,
    VaultAnimationController,
    VaultAnimationControllerUpgraded,
    PryAnimation,
    JudgementAnimation,
    AutoclaveAnimationV2,
    GlaiveSweepAnimation,
    AutoclaveFailureAnimation
)

from .mandible_foreman import (
    JawClamp,
    JawRelease,
    ViseroyTrap,
    ViseroyRelease,
    SiteInspectionBuff,
    SiteInspectionScan,
    SiteInspectionScanUpgraded,
    ExpediteRush,
    JawlineNetwork,
    JawlineNetworkUpgraded
)

from .potpourrist import (
    PedestalStrike,
    InfuseEffect,
    DemiluneSwing,
    SelenicBackdraftZone,
    LunacyEffect,
    GraniteGeasEffect,
    GeasBreakHeal,
    MelangeEminence,
    MelangeEminenceHealAnimation,
    MelangeEminenceInfusedHealAnimation
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
    AuctionCurseTickAnimation,
    MarketFuturesAnimation,
    MarketFuturesTeleportAnimation,
    DeftRerollAnimation,
)

from .marrow_condenser import (
    OssifyAnimation,
    BoneTitheAnimation,
    BoneTitheDeathHealAnimation,
    BoneChunkProjectile,
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
    DerelictPushTrail,
    DerelictBuildingFormation,
    DerelictBuildingTiles,
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
    DivergeAnimationUpgraded,
    AerosolizeArmsAnimation,
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
    # Core Animations
    'RespawnAnimation',
    # Glaiveman
    'SpinningGlaiveProjectile',
    'LightningBolt',
    'CrossBeam',
    'AutoclaveAnimation',
    'PryImpactAnimation',
    'VaultAnimationController',
    'VaultAnimationControllerUpgraded',
    'PryAnimation',
    'JudgementAnimation',
    'AutoclaveAnimationV2',
    'GlaiveSweepAnimation',
    'AutoclaveFailureAnimation',
    # Mandible Foreman
    'JawClamp',
    'JawRelease',
    'ViseroyTrap',
    'ViseroyRelease',
    'SiteInspectionBuff',
    'SiteInspectionScan',
    'SiteInspectionScanUpgraded',
    'ExpediteRush',
    'JawlineNetwork',
    'JawlineNetworkUpgraded',
    # Potpourrist
    'PedestalStrike',
    'InfuseEffect',
    'DemiluneSwing',
    'SelenicBackdraftZone',
    'LunacyEffect',
    'GraniteGeasEffect',
    'GeasBreakHeal',
    'MelangeEminence',
    'MelangeEminenceHealAnimation',
    'MelangeEminenceInfusedHealAnimation',
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
    'AuctionCurseTickAnimation',
    'MarketFuturesAnimation',
    'MarketFuturesTeleportAnimation',
    'DeftRerollAnimation',
    # Marrow Condenser
    'OssifyAnimation',
    'BoneTitheAnimation',
    'BoneTitheAnimationUpgraded',
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
    'DerelictPushTrail',
    'DerelictBuildingFormation',
    'DerelictBuildingTiles',
    # Fowl Contrivance
    'ParabolAnimation',
    'FragcrestAnimation',
    'GaussianDuskChargeAnimation',
    'GaussianDuskFireAnimation',
    'RailGenesisDeathExplosionAnimation',
    # Gas Machinist
    'VaporSpawnAnimation',
    'DivergeAnimation',
    'DivergeAnimationUpgraded',
    'AerosolizeArmsAnimation',
    'VaporAOETickAnimation',
    # Factory
    'AnimationFactory',
]
