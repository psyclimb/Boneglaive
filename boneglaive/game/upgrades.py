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
            "description": "If Judgement kills a target, the cooldown is refreshed.",
            "type": "buff",
            "cost": 1
        }
    },
    "MANDIBLE_FOREMAN": {
        "Viseroy": {
            "name": "Viseroy",
            "description": "Increases initial trap damage by 1. Adds a 1 turn disarm when trap is applied. Disarm has a 3 turn cooldown.",
            "type": "buff",
            "cost": 1
        },
        "Expedite": {
            "name": "Expedite",
            "description": "Increase damage by 2. Decrease cooldown by 1.",
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
            "description": "GRAYMAN becomes completely inert. Move range reduced to 0. Delta Config cooldown reduced by 6. Græ Exchange cooldown reduced by 1. +1 PRT.",
            "type": "sidegrade",
            "cost": 1
        },
        "Delta Config": {
            "name": "Delta Config",
            "description": "Abducts all adjacent enemies and takes them to the target location.",
            "type": "buff",
            "cost": 1
        },
        "Estrange": {
            "name": "Estrange",
            "description": "Estranging an already estranged target banishes them and spawns a GRAYMAN echo.",
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
            "description": "Half of infused Demilune's damage pierces defense. Infused Granite Geas deals +1 damage.",
            "type": "buff",
            "cost": 1
        },
        "Demilune": {
            "name": "Demilune",
            "description": "After swinging, creates a mirrored crescent zone in the opposite direction. Enemies within cannot attack POTPOURRIST.",
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
            "description": "Flashes the primary target.",
            "type": "buff",
            "cost": 1
        },
        "Neural Shunt": {
            "name": "Neural Shunt",
            "description": "Increases range by 2. Damage increased by 2. No longer flashes.",
            "type": "buff",
            "cost": 1
        },
        "Karrier Rave": {
            "name": "Karrier Rave",
            "description": "Allows walking through units while active.",
            "type": "buff",
            "cost": 1
        },
        "Scalar Node": {
            "name": "Scalar Node",
            "description": "Trap damage pierces defense. Increase range by 1.",
            "type": "buff",
            "cost": 1
        }
    },
    "FOWL_CONTRIVANCE": {
        "Rail Genesis": {
            "name": "Rail Genesis",
            "description": "Rail junctions grant bonuses: Parabol max range +1, attack +1, attack range +2, defense +1.",
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
            "description": "Allows ground targetting placement as a silent trap. Arms after 1 turn. Lasts 6 turns.",
            "type": "sidegrade",
            "cost": 1
        }
    },
    "GAS_MACHINIST": {
        "Effluvium Lathe": {
            "name": "Effluvium Lathe",
            "description": "Unlocks Aerosolize Arms: Disarm target and spawn LIVING AEROSOL controlled by that player.",
            "type": "buff",
            "cost": 1
        },
        "Broaching Gas": {
            "name": "Broaching Gas",
            "description": "Increases damage by 3.",
            "type": "buff",
            "cost": 1
        },
        "Saft-E-Gas": {
            "name": "Saft-E-Gas",
            "description": "Grants +1 PRT instead of +1 DEF. Increase heal tick by 1.",
            "type": "buff",
            "cost": 1
        },
        "Diverge": {
            "name": "Diverge",
            "description": "Adds Calibration Gas as a 3rd vapor: resets all units in cloud to base stats.",
            "type": "buff",
            "cost": 1
        }
    },
    "DERELICTIONIST": {
        "Severance": {
            "name": "Severance",
            "description": "Allows passage through furniture and terrain while active.",
            "type": "buff",
            "cost": 1
        },
        "Vagal Run": {
            "name": "Vagal Run",
            "description": "Allows targeting enemy units.",
            "type": "buff",
            "cost": 1
        },
        "Derelict": {
            "name": "Derelict",
            "description": "Creates an old decrepit building in a 3x3 circle around units affected by Derelicted.",
            "type": "buff",
            "cost": 1
        },
        "Partition": {
            "name": "Partition",
            "description": "Allows self cast and reduces the cooldown of the dissociation save from 8 to 6.",
            "type": "buff",
            "cost": 1
        }
    },
    "MARROW_CONDENSER": {
        "Dominion": {
            "name": "Dominion",
            "description": "Each kill inside Marrow Dike grants +1 attack.",
            "type": "buff",
            "cost": 1
        },
        "Ossify": {
            "name": "Ossify",
            "description": "Reflects 1 damage back to attackers.",
            "type": "buff",
            "cost": 1
        },
        "Marrow Dike": {
            "name": "Marrow Dike",
            "description": "Pull damage increased from 3 to 4. Mired enemies take 1 damage per turn.",
            "type": "buff",
            "cost": 1
        },
        "Bone Tithe": {
            "name": "Bone Tithe",
            "description": "Area increased to range 2 (5x5 instead of 3x3).",
            "type": "buff",
            "cost": 1
        }
    },
    "PELOTARI": {
        "Riposte": {
            "name": "Riposte",
            "description": "Increases def and ball count to 8.",
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

        # Special handling for Rail Genesis upgrade - mark junctions
        from boneglaive.utils.constants import UnitType
        if unit.type == UnitType.FOWL_CONTRIVANCE and skill_name == "Rail Genesis":
            # Calculate junction coordinates
            center_y = game.map.height // 2
            center_x = game.map.width // 2

            # Horizontal lines
            top_horizontal = 1
            middle_horizontal = center_y - 2
            bottom_horizontal = game.map.height - 2

            # Vertical lines
            vertical_line_1 = center_x - 2
            vertical_line_2 = center_x + 2

            # Mark all 6 junction positions
            if not hasattr(game.map, 'junction_positions'):
                game.map.junction_positions = set()
            game.map.junction_positions.add((top_horizontal, vertical_line_1))
            game.map.junction_positions.add((top_horizontal, vertical_line_2))
            game.map.junction_positions.add((middle_horizontal, vertical_line_1))
            game.map.junction_positions.add((middle_horizontal, vertical_line_2))
            game.map.junction_positions.add((bottom_horizontal, vertical_line_1))
            game.map.junction_positions.add((bottom_horizontal, vertical_line_2))

        # Special handling for Effluvium Lathe upgrade - unlock Aerosolize Arms skill
        if unit.type == UnitType.GAS_MACHINIST and skill_name == "Effluvium Lathe":
            from boneglaive.game.skills.gas_machinist import AerosolizeArmsSkill
            # Add Aerosolize Arms to the unit's active skills
            aerosolize_skill = AerosolizeArmsSkill()
            unit.active_skills.append(aerosolize_skill)

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
