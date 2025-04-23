#!/usr/bin/env python3
"""
Registry for unit skills and abilities.
This module maps each unit type to its available skills.
"""

# Import all skill classes
from boneglaive.game.skills.glaiveman import (
    Autoclave, PrySkill, VaultSkill, JudgementThrowSkill
)

from boneglaive.game.skills.mandible_foreman import (
    Viseroy, DischargeSkill, SiteInspectionSkill, JawlineSkill
)

from boneglaive.game.skills.grayman import (
    Stasiality, DeltaConfigSkill, EstrangeSkill, GraeExchangeSkill
)

# Define the skills available for each unit type
UNIT_SKILLS = {
    "GLAIVEMAN": {
        "passive": Autoclave(),
        "active": [PrySkill(), VaultSkill(), JudgementThrowSkill()]
    },
    "MANDIBLE_FOREMAN": {
        "passive": Viseroy(),
        "active": [DischargeSkill(), SiteInspectionSkill(), JawlineSkill()]
    },
    "GRAYMAN": {
        "passive": Stasiality(),
        "active": [DeltaConfigSkill(), EstrangeSkill(), GraeExchangeSkill()]
    }
}