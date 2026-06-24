#!/usr/bin/env python3
"""
Registry for unit skills and abilities.
This module maps each unit type to its available skills.
"""

from boneglaive.utils.constants import UnitType

# Import all skill classes
from boneglaive.game.skills.glaiveman import (
    Autoclave, PrySkill, VaultSkill, JudgementSkill
)

from boneglaive.game.skills.mandible_foreman import (
    Viseroy, DischargeSkill, SiteInspectionSkill, JawlineSkill
)

from boneglaive.game.skills.grayman import (
    Stasiality, DeltaConfigSkill, EstrangeSkill, GraeExchangeSkill
)

from boneglaive.game.skills.marrow_condenser import (
    Dominion, OssifySkill, MarrowDikeSkill, BoneTitheSkill
)

from boneglaive.game.skills.fowl_contrivance import (
    RailGenesis, GaussianDuskSkill, BigArcSkill, FragcrestSkill
)

from boneglaive.game.skills.gas_machinist import (
    EffluviumLathe, EnbroachmentGasSkill, SaftEGasSkill, DivergeSkill
)

from boneglaive.game.skills.delphic_appraiser import (
    ValuationOracle, MarketFuturesSkill, AuctionCurseSkill, DivineDrepreciationSkill
)

from boneglaive.game.skills.interferer import (
    NeutronIlluminant, NeuralShuntSkill, KarrierRaveSkill, ScalarNodeSkill
)

from boneglaive.game.skills.derelictionist import (
    Severance, VagalRunSkill, DerelictSkill, PartitionSkill
)

from boneglaive.game.skills.potpourrist import (
    MelangeEminence, InfuseSkill, DemiluneSkill, GraniteGeasSkill
)

from boneglaive.game.skills.landscaper import (
    TranslativeStroke, HornswoggleSkill, TopiaryBreathSkill, DissonanceSkill
)

from boneglaive.game.skills.ordnance_graft import (
    Quadcopter, InoculantSkill, DroneInoculantSkill, SkyhookSkill, HarvestSkill
)

# Define the skills available for each unit type
UNIT_SKILLS = {
    UnitType.GLAIVEMAN: {
        "passive": Autoclave(),
        "active": [PrySkill(), VaultSkill(), JudgementSkill()]
    },
    UnitType.MANDIBLE_FOREMAN: {
        "passive": Viseroy(),
        "active": [DischargeSkill(), SiteInspectionSkill(), JawlineSkill()]
    },
    UnitType.GRAYMAN: {
        "passive": Stasiality(),
        "active": [DeltaConfigSkill(), EstrangeSkill(), GraeExchangeSkill()]
    },
    UnitType.MARROW_CONDENSER: {
        "passive": Dominion(),
        "active": [OssifySkill(), MarrowDikeSkill(), BoneTitheSkill()]
    },
    UnitType.FOWL_CONTRIVANCE: {
        "passive": RailGenesis(),
        "active": [GaussianDuskSkill(), BigArcSkill(), FragcrestSkill()]
    },
    UnitType.GAS_MACHINIST: {
        "passive": EffluviumLathe(),
        "active": [EnbroachmentGasSkill(), SaftEGasSkill(), DivergeSkill()]
    },
    UnitType.DELPHIC_APPRAISER: {
        "passive": ValuationOracle(),
        "active": [MarketFuturesSkill(), AuctionCurseSkill(), DivineDrepreciationSkill()]
    },
    UnitType.INTERFERER: {
        "passive": NeutronIlluminant(),
        "active": [NeuralShuntSkill(), KarrierRaveSkill(), ScalarNodeSkill()]
    },
    UnitType.DERELICTIONIST: {
        "passive": Severance(),
        "active": [VagalRunSkill(), DerelictSkill(), PartitionSkill()]
    },
    UnitType.POTPOURRIST: {
        "passive": MelangeEminence(),
        "active": [InfuseSkill(), DemiluneSkill(), GraniteGeasSkill()]
    },
    UnitType.LANDSCAPER: {
        "passive": TranslativeStroke(),
        "active": [HornswoggleSkill(), TopiaryBreathSkill(), DissonanceSkill()]
    },
    UnitType.ORDNANCE_GRAFT: {
        "passive": Quadcopter(),
        "active": [InoculantSkill(), SkyhookSkill(), HarvestSkill()]
    },
    # ORDNANCE_DRONE is player-piloted (leashed within ORDNANCE_DRONE_LEASH of the graft).
    # Its basic attack is a plain hit (its ATK stat); it grafts bombs via its OWN Inoculant
    # (DroneInoculantSkill — a separate class for independent balance, shown as "Inoculant"
    # with a drone-specific icon). Not recruitable, so the completeness guard exempts it.
    UnitType.ORDNANCE_DRONE: {
        "active": [DroneInoculantSkill()]
    },
}

# Fail loudly at import time if a newly added unit is incompletely wired —
# missing skills, upgrades, or help. This catches the silent gaps that otherwise
# only surface during playtest. Asset-file checks are excluded here (assets live
# outside the source tree); the test harness runs those with require_assets=True.
from boneglaive.game.unit_validation import require_complete_unit_registration
require_complete_unit_registration()
