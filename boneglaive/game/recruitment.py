#!/usr/bin/env python3
"""Recruitment/selection order for the setup phase."""

from boneglaive.utils.constants import UNIT_DESCRIPTORS


# Recruitment/selection order, derived from the descriptor table. HEINOUS_VAPOR
# (a summon) is excluded because it is marked non-recruitable.
RECRUITMENT_ORDER = [d.unit_type for d in UNIT_DESCRIPTORS if d.recruitable]
