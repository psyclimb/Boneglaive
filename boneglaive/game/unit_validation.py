#!/usr/bin/env python3
"""Startup completeness check for unit registration — turns silent gaps loud.

Adding a unit touches many tables; most fail *silently* if forgotten (no skills'
upgrades, blank help, missing art) so the unit ships half-wired and you only
notice in playtest. This module gathers those checks in one place so a forgotten
step becomes a loud error instead.

The code/data checks (skills, upgrades, help) are headless and run at import via
registry.py. The asset checks (sprite/icon SVGs) are environment-dependent —
assets live outside the GPL source tree and are absent in CI — so they are opt-in
(`require_assets=True`) and meant for the dev-side test harness, not import.
"""

import os
from typing import List

from boneglaive.utils.constants import UNIT_DESCRIPTORS
from boneglaive.utils.paths import asset_path


def _skill_names(skills: dict) -> set:
    """The set of a unit's skill .name strings (passive + actives)."""
    names = {skills["passive"].name}
    names.update(s.name for s in skills["active"])
    return names


def validate_unit_registration(require_assets: bool = False) -> List[str]:
    """Return a list of human-readable problems with unit wiring (empty == clean).

    Checks every recruitable unit has: a skill set (passive + 3 actives), an
    upgrade entry whose keys match its skills exactly, and a long-form help
    entry. With require_assets, also checks the sprite and skill-icon SVGs exist.
    """
    # Imported here (not at module top) so this leaf-ish module can be pulled in
    # by registry.py without an import cycle.
    from boneglaive.game.skills.registry import UNIT_SKILLS
    from boneglaive.game.upgrades import SKILL_UPGRADES
    from boneglaive.utils.unit_help_data import get_unit_help_data

    problems: List[str] = []
    help_data = get_unit_help_data()

    for d in UNIT_DESCRIPTORS:
        if not d.recruitable:
            continue
        unit = d.unit_type
        name = unit.name

        # --- skills ---
        skills = UNIT_SKILLS.get(unit)
        if not skills:
            problems.append(f"{name}: no UNIT_SKILLS entry (registry.py)")
            # Everything below needs the skill list; skip the rest for this unit.
            continue
        if "passive" not in skills or len(skills.get("active", [])) != 3:
            problems.append(
                f"{name}: skill set must be 1 passive + 3 actives (registry.py)")
            continue
        names = _skill_names(skills)

        # --- upgrades (one per skill, keys must match skill names) ---
        upgrades = SKILL_UPGRADES.get(unit)
        if not upgrades:
            problems.append(f"{name}: no SKILL_UPGRADES entry (upgrades.py)")
        else:
            missing = names - set(upgrades)
            extra = set(upgrades) - names
            if missing:
                problems.append(
                    f"{name}: skills with no upgrade: {sorted(missing)} (upgrades.py)")
            if extra:
                problems.append(
                    f"{name}: upgrade keys not matching any skill name "
                    f"(typo?): {sorted(extra)} (upgrades.py)")

        # --- long-form help ---
        if unit not in help_data:
            problems.append(f"{name}: no help entry (unit_help_data.py)")

        # --- art assets (opt-in; dev environment only) ---
        if require_assets:
            sprite = asset_path(f"graphics/units/{name.lower()}.svg")
            if not os.path.exists(sprite):
                problems.append(f"{name}: missing sprite {sprite}")
            for skill_name in names:
                icon_name = skill_name.lower().replace(' ', '_')
                icon = asset_path(f"graphics/skill_icons/{icon_name}.svg")
                if not os.path.exists(icon):
                    problems.append(
                        f"{name}: missing skill icon for '{skill_name}' ({icon})")

    return problems


def require_complete_unit_registration() -> None:
    """Raise RuntimeError listing every incomplete unit (code/data checks only)."""
    problems = validate_unit_registration(require_assets=False)
    if problems:
        raise RuntimeError(
            "Incomplete unit registration:\n  - " + "\n  - ".join(problems))
