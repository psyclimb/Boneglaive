#!/usr/bin/env python3
"""
Sound Registry for Boneglaive
Maps skill names, actions, and events to sound files.
"""

# Sound registry: maps event/skill names to sound keys
# Sound keys are filenames (without extension)
# The SoundManager looks for sounds/<category>/<sound_key>.ogg (preferred,
# falling back to .wav). The path strings in the value column below are
# documentation only; the loader builds the real path from the key.

SKILL_SOUNDS = {
    # GLAIVEMAN skills (primary skill sound - played by AnimationFactory)
    "JUDGEMENT": "judgement",
    "PRY": "pry",
    "VAULT": "vault",
    "VAULT_UPGRADED": "vault_enhanced",
    "AUTOCLAVE": "autoclave",
    "GLAIVE_SWEEP": "glaive_sweep",

    # MANDIBLE FOREMAN skills
    "EXPEDITE": "expedite",
    "DISCHARGE": "viseroy_release",
    "SITE_INSPECTION": "site_inspection",
    "SITE_INSPECTION_UPGRADED": "site_inspection_enhanced",
    "JAWLINE": "jawline",
    "JAWLINE_UPGRADED": "jawline_enhanced",
    "VISEROY": "viseroy_trap",
    "VISEROY_TICK": "jaw_tighten",

    # POTPOURRIST skills
    "PEDESTAL_STRIKE": "pedestal_strike",
    "INFUSE": "infuse",
    "DEMILUNE": "demilune",
    "DEMILUNE_INFUSED": "demilune_infused",
    "SELENIC_BACKDRAFT": "selenic_backdraft",
    "GRANITE_GEAS": "granite_geas",
    "MELANGE_EMINENCE_HEAL": "melange_heal",
    "MELANGE_EMINENCE_INFUSED_HEAL": "melange_heal_infused",

    # GRAYMAN skills
    "DELTA_CONFIG": "delta_config",
    "ESTRANGE": "estrange",
    "GRÆ_EXCHANGE": "grae_exchange",
    "GRAYMAN_DOPPELGANGER_DEATH": "grayman_doppelganger_death",

    # MARROW CONDENSER skills
    "OSSIFY": "ossify",
    "MARROW_DIKE": "marrow_dike",
    "BONE_TITHE": "bone_tithe",
    "MARROW_DIKE_WALL_DESPAWN": "marrow_dike_despawn",

    # FOWL CONTRIVANCE skills
    "GAUSSIAN_DUSK": "gaussian_dusk",
    "BIG_ARC": "parabol",
    "PARABOL": "parabol",
    "FRAGCREST": "fragcrest",
    "RAIL_GENESIS_DEATH_EXPLOSION": "rail_genesis_death",

    # GAS MACHINIST skills
    "BROACHING_GAS": "vapor_spawn",
    "SAFT_E_GAS": "vapor_spawn",
    "COOLANT_GAS": "vapor_spawn",
    "CUTTING_GAS": "vapor_spawn",
    "CALIBRATION_GAS": "vapor_spawn",
    "LIVING_AEROSOL_GAS": "vapor_spawn",
    "DIVERGE": "diverge",
    "AEROSOLIZE_ARMS": "aerosolize_arms",
    "VAPOR_AOE_BROACHING": "vapor_tick_broaching",
    "VAPOR_AOE_SAFETY": "vapor_tick_safety",
    "VAPOR_AOE_COOLANT": "vapor_tick_coolant",
    "VAPOR_AOE_CUTTING": "vapor_tick_cutting",
    "VAPOR_AOE_CALIBRATION": "vapor_tick_calibration",

    # DELPHIC APPRAISER skills
    "MARKET_FUTURES": "market_futures",
    "AUCTION_CURSE": "auction_curse",
    "AUCTION_CURSE_TICK": "auction_curse_tick",
    "DIVINE_DEPRECIATION": "divine_depreciation",
    "DEFT(?)_REROLL": "deft_reroll",
    "PARALLAX": "parallax",

    # INTERFERER skills
    "NEUTRON_ILLUMINANT_CARDINAL": "neutron_illuminant",
    "NEUTRON_ILLUMINANT_DIAGONAL": "neutron_illuminant",
    "NEURAL_SHUNT": "neural_shunt",
    "KARRIER_RAVE": "karrier_rave",
    "KARRIER_RAVE_STRIKE": "karrier_rave_strike",
    "SCALAR_NODE": None,  # Silent trap placement

    # DERELICTIONIST skills
    "VAGAL_RUN": "vagal_run",
    "VAGAL_RUN_ABREACTION": "vagal_run_delayed",
    "PARTITION": "partition",
    "DERELICT_BUILDING_FORMATION": "building_formation",
    "DERELICT_BUILDING_TILES": None,  # Persistent tiles (silent)

    # LANDSCAPER skills
    "HORNSWOGGLE": "hornswoggle",
    "TOPIARY_BREATH": "topiary_breath",
    "DISSONANCE": "dissonance",

    # ORDNANCE GRAFT skills
    "INOCULANT": "inoculant",
    "SKYHOOK": "skyhook",
    "HARVEST": "harvest",
}
def get_sound_for_skill(skill_name: str) -> str:
    """
    Get the sound key for a skill name.

    Args:
        skill_name: Skill name (e.g., "Estrange", "JUDGEMENT")

    Returns:
        Sound key (filename without extension), or None if no sound defined
    """
    # Normalize skill name (uppercase, replace spaces/hyphens with underscores)
    skill_key = skill_name.upper().replace(" ", "_").replace("-", "_")
    return SKILL_SOUNDS.get(skill_key)
