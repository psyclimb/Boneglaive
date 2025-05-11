#!/usr/bin/env python3
"""
Registry for unit skills and abilities.
This module maps each unit type to its available skills.
"""

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
    WretchedDecension, MurmurationDuskSkill, FlapSkill, EmeticFlangeSkill
)

from boneglaive.game.skills.gas_machinist import (
    EffluviumLathe, EnbroachmentGasSkill, SaftEGasSkill, DivergeSkill
)

from boneglaive.game.skills.delphic_appraiser import (
    ValuationOracle, MarketFuturesSkill, AuctionCurseSkill, DivineDrepreciationSkill
)

# Define the skills available for each unit type
UNIT_SKILLS = {
    "GLAIVEMAN": {
        "passive": Autoclave(),
        "active": [PrySkill(), VaultSkill(), JudgementSkill()]
    },
    "MANDIBLE_FOREMAN": {
        "passive": Viseroy(),
        "active": [DischargeSkill(), SiteInspectionSkill(), JawlineSkill()]
    },
    "GRAYMAN": {
        "passive": Stasiality(),
        "active": [DeltaConfigSkill(), EstrangeSkill(), GraeExchangeSkill()]
    },
    "MARROW_CONDENSER": {  # Displayed as "MARROW CONDENSER" in-game
        "passive": Dominion(),
        "active": [OssifySkill(), MarrowDikeSkill(), BoneTitheSkill()]
    },
    "FOWL_CONTRIVANCE": {
        "passive": WretchedDecension(),
        "active": [MurmurationDuskSkill(), FlapSkill(), EmeticFlangeSkill()]
    },
    "GAS_MACHINIST": {
        "passive": EffluviumLathe(),
        "active": [EnbroachmentGasSkill(), SaftEGasSkill(), DivergeSkill()]
    },
    "DELPHIC_APPRAISER": {
        "passive": ValuationOracle(),
        "active": [MarketFuturesSkill(), AuctionCurseSkill(), DivineDrepreciationSkill()]
    }
}