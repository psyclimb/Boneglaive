#!/usr/bin/env python3
"""
Skills and abilities system for Boneglaive units.
This module is the entry point for all skill-related functionality.
"""

# Core functionality
from boneglaive.game.skills.core import (
    Skill, 
    ActiveSkill, 
    PassiveSkill,
    SkillType,
    TargetType
)

# Unit-specific skills
from boneglaive.game.skills.glaiveman import (
    Autoclave,
    PrySkill, 
    VaultSkill, 
    JudgementSkill
)

from boneglaive.game.skills.mandible_foreman import (
    Viseroy,
    DischargeSkill, 
    SiteInspectionSkill, 
    JawlineSkill
)

from boneglaive.game.skills.grayman import (
    Stasiality,
    DeltaConfigSkill, 
    EstrangeSkill, 
    GraeExchangeSkill
)

# Define the skills available for each unit type
from boneglaive.game.skills.registry import UNIT_SKILLS