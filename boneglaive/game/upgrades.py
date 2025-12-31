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
    "GLAIVEMAN": {
        "Autoclave": {
            "name": "Autoclave",
            "description": "After Autoclave triggers, another glaive counter attack is prepared.",
            "type": "buff",
            "cost": 1
        },
        "Pry": {
            "name": "Pry",
            "description": "Move penalty increased from -1 to -2.",
            "type": "buff",
            "cost": 1
        },
        "Vault": {
            "name": "Vault",
            "description": "Range increased from 2 to 3. Added landing area damage.",
            "type": "buff",
            "cost": 1
        },
        "Judgement": {
            "name": "Judgement",
            "description": "If Judgement kills a target, cooldown reduced by 2.",
            "type": "buff",
            "cost": 1
        }
    },
    "MANDIBLE_FOREMAN": {
        "Viseroy": {
            "name": "Viseroy",
            "description": "Adds a 1 turn disarm when trap is applied. Disarm has a 3 turn cooldown.",
            "type": "buff",
            "cost": 1
        },
        "Expedite": {
            "name": "Expedite",
            "description": "Range increased from 4 to 5. Grants +2 defense for 1 turn after use.",
            "type": "buff",
            "cost": 1
        },
        "Site Inspection": {
            "name": "Site Inspection",
            "description": "Enhanced bonuses at all terrain levels. Adds +1 defense to clear areas. Obstructed areas now grant benefits.",
            "type": "buff",
            "cost": 1
        },
        "Jawline": {
            "name": "Jawline",
            "description": "Transforms into a directional 3x9 tile line. Blocked by terrain.",
            "type": "buff",
            "cost": 1
        }
    },
    "GRAYMAN": {
        "Stasiality": {
            "name": "Stasiality",
            "description": "Adds an active ability to enter stasis for 1 turn. Invulnerable but cannot act.",
            "type": "buff",
            "cost": 1
        },
        "Estrange": {
            "name": "Estrange",
            "description": "Estranging an already estranged target banishes them and spawns a GRAYMAN echo.",
            "type": "buff",
            "cost": 1
        },
        "Delta Config": {
            "name": "Delta Config",
            "description": "Abducts all adjacent enemies and takes them to the target location.",
            "type": "buff",
            "cost": 1
        },
        "Græ Exchange": {
            "name": "Græ Exchange",
            "description": "Echoes can use Græ Exchange.",
            "type": "buff",
            "cost": 1
        }
    },
    "DELPHIC_APPRAISER": {
        "Valuation Oracle": {
            "name": "Valuation Oracle",
            "description": "Enemy units are assigned astral values and treated as furniture.",
            "type": "buff",
            "cost": 1
        },
        "Market Futures": {
            "name": "Market Futures",
            "description": "Imbued furniture provides Valuation Oracle bonuses to adjacent allies.",
            "type": "buff",
            "cost": 1
        },
        "Auction Curse": {
            "name": "Auction Curse",
            "description": "If target's HP equals curse duration when applied and they die while cursed, award +1 GP.",
            "type": "buff",
            "cost": 1
        },
        "Divine Depreciation": {
            "name": "Divine Depreciation",
            "description": "Allows a second reroll of all furniture values.",
            "type": "buff",
            "cost": 1
        }
    },
    "POTPOURRIST": {
        "Melange Eminence": {
            "name": "Melange Eminence",
            "description": "Heals 4 HP upon upgrading. Increases max HP from 24 to 28.",
            "type": "buff",
            "cost": 1
        },
        "Infuse": {
            "name": "Infuse",
            "description": "Infused Demilune reduces enemy defense to 0. Infused Granite Geas deals +1 damage.",
            "type": "buff",
            "cost": 1
        },
        "Demilune": {
            "name": "Demilune",
            "description": "After swinging, places bowl of potpourri in the opposite direction, creating a mirrored crescent zone. Enemies within cannot attack POTPOURRIST.",
            "type": "buff",
            "cost": 1
        },
        "Granite Geas": {
            "name": "Granite Geas",
            "description": "Target's attack is treated as 2 when attacking POTPOURRIST.",
            "type": "buff",
            "cost": 1
        }
    },
    "INTERFERER": {
        "Neutron Illuminant": {
            "name": "Neutron Illuminant",
            "description": "Flash covers all adjacent tiles.",
            "type": "buff",
            "cost": 1
        },
        "Neural Shunt": {
            "name": "Neural Shunt",
            "description": "Range increased from 1 to 3. No longer flashes.",
            "type": "buff",
            "cost": 1
        },
        "Karrier Rave": {
            "name": "Karrier Rave",
            "description": "Adds an extra hit and gives +1 move while active.",
            "type": "buff",
            "cost": 1
        },
        "Scalar Node": {
            "name": "Scalar Node",
            "description": "Trap damage pierces defense.",
            "type": "buff",
            "cost": 1
        }
    },
    "FOWL_CONTRIVANCE": {
        "Rail Genesis": {
            "name": "Rail Genesis",
            "description": "Applies shrapnel to adjacent enemies when rails are destroyed.",
            "type": "buff",
            "cost": 1
        },
        "Gaussian Dusk": {
            "name": "Gaussian Dusk",
            "description": "Weaponizes the curve's extremes: executes enemies ≤25% HP, shreds defense to 0 for 2 turns on enemies ≥87.5% HP.",
            "type": "buff",
            "cost": 1
        },
        "Parabol": {
            "name": "Parabol",
            "description": "Shell continues through a mirrored underground parabola. Second explosion swaps furniture positions with enemy positions from the first explosion.",
            "type": "buff",
            "cost": 1
        },
        "Fragcrest": {
            "name": "Fragcrest",
            "description": "Turns into a 5x5 self-targeted AOE.",
            "type": "sidegrade",
            "cost": 1
        }
    },
    "GAS_MACHINIST": {
        "Diverge": {
            "name": "Diverge",
            "description": "Adds Calibrating Gas as a 3rd vapor: resets all units in cloud to base stats.",
            "type": "buff",
            "cost": 1
        },
        "Effluvium Lathe": {
            "name": "Effluvium Lathe",
            "description": "Target an ally to spawn a leashed vapor weapon. Matches ally's attack. Follows at 1 tile distance.",
            "type": "buff",
            "cost": 1
        }
    },
    # More units can be added here
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
            if ut == unit.type:  # Compare enum to enum, not value
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
            if ut == unit.type:  # Compare enum to enum, not value
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
