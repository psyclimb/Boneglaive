#!/usr/bin/env python3
"""
Upgrade System for Boneglaive
Defines skill and passive upgrades for all units.
"""

from typing import Optional, Dict, List, Set
from boneglaive.utils.message_log import message_log, MessageType

# ============================================================================
# UPGRADE DEFINITIONS
# ============================================================================

SKILL_UPGRADES = {
    # Unit upgrades will be defined here
    # Format: "UNIT_TYPE_NAME": { "SkillName": { upgrade_def }, ... }
}

# ============================================================================
# UPGRADE MANAGER CLASS
# ============================================================================

class UpgradeManager:
    """Manages skill and passive upgrades for units."""

    @staticmethod
    def can_afford_upgrade(game, player: int, upgrade_cost: int = 1) -> bool:
        """Check if player has enough upgrade points."""
        points = game.player1_upgrade_points if player == 1 else game.player2_upgrade_points
        return points >= upgrade_cost

    @staticmethod
    def get_available_upgrades(unit) -> List[Dict]:
        """
        Get list of upgrades available for this unit.
        Returns list of dicts with: skill_name, name, description, type, cost
        """
        from boneglaive.utils.constants import UnitType

        # Get unit type name
        unit_type_name = None
        for ut in UnitType:
            if ut.value == unit.type:
                unit_type_name = ut.name
                break

        if not unit_type_name or unit_type_name not in SKILL_UPGRADES:
            return []

        upgrades = []
        for skill_name, upgrade_def in SKILL_UPGRADES[unit_type_name].items():
            # Check if not already upgraded
            if hasattr(unit, 'upgraded_skills') and skill_name in unit.upgraded_skills:
                continue

            upgrades.append({
                'skill_name': skill_name,
                'name': upgrade_def['name'],
                'description': upgrade_def['description'],
                'type': upgrade_def['type'],
                'cost': upgrade_def['cost']
            })

        return upgrades

    @staticmethod
    def apply_upgrade(unit, skill_name: str, game) -> bool:
        """
        Apply an upgrade to a unit's skill.
        Returns True if successful, False if upgrade failed.
        """
        # Verify unit has upgraded_skills attribute
        if not hasattr(unit, 'upgraded_skills'):
            unit.upgraded_skills = set()

        # Check if already upgraded
        if skill_name in unit.upgraded_skills:
            return False

        # Check if player can afford
        upgrade_cost = 1  # All upgrades cost 1 for now
        if not UpgradeManager.can_afford_upgrade(game, unit.player, upgrade_cost):
            return False

        # Apply upgrade
        unit.upgraded_skills.add(skill_name)

        # Deduct upgrade point
        if unit.player == 1:
            game.player1_upgrade_points -= upgrade_cost
        else:
            game.player2_upgrade_points -= upgrade_cost

        # Log upgrade message
        from boneglaive.utils.constants import UnitType
        unit_type_name = None
        for ut in UnitType:
            if ut.value == unit.type:
                unit_type_name = ut.name
                break

        upgrade_name = "Unknown"
        if unit_type_name in SKILL_UPGRADES and skill_name in SKILL_UPGRADES[unit_type_name]:
            upgrade_name = SKILL_UPGRADES[unit_type_name][skill_name]['name']

        message_log.add_message(
            f"Player {unit.player} upgraded {unit.get_display_name()}'s {skill_name} → {upgrade_name}",
            MessageType.SYSTEM,
            player=unit.player
        )

        return True

    @staticmethod
    def is_skill_upgraded(unit, skill_name: str) -> bool:
        """Check if a specific skill is upgraded on this unit."""
        return hasattr(unit, 'upgraded_skills') and skill_name in unit.upgraded_skills
