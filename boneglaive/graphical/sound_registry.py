#!/usr/bin/env python3
"""
Sound Registry for Boneglaive
Maps skill names, actions, and events to sound files.
"""

# Sound registry: maps event/skill names to sound keys
# Sound keys are filenames (without .wav extension)
# The SoundManager will look for these in sounds/<category>/<sound_key>.wav

SKILL_SOUNDS = {
    # GLAIVEMAN skills
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
    "GRAE_EXCHANGE": "grae_exchange",
    "GRÆ_EXCHANGE": "grae_exchange",
    "GRAYMAN_ECHO_DEATH": "grayman_echo_death",

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
    "VAPOR_AOE_BROACHING": "vapor_tick",
    "VAPOR_AOE_SAFETY": "vapor_tick",
    "VAPOR_AOE_COOLANT": "vapor_tick",
    "VAPOR_AOE_CUTTING": "vapor_tick",
    "VAPOR_AOE_CALIBRATION": "vapor_tick",

    # DELPHIC APPRAISER skills
    "MARKET_FUTURES": "market_futures",
    "AUCTION_CURSE": "auction_curse",
    "AUCTION_CURSE_TICK": "auction_curse_tick",
    "DIVINE_DEPRECIATION": "divine_depreciation",
    "DEFT(?) REROLL": "deft_reroll",
    "DEFT(?)_REROLL": "deft_reroll",
    "DEFT_REROLL": "deft_reroll",
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

    # PELOTARI skills (DLC)
    "MATADOR": "matador",
    "POACH": "poach",
    "BACKHAND": "backhand",
    "BACKHAND_REFLECTION": "backhand_reflection",
}

# Impact sounds (hit effects, explosions, etc.)
IMPACT_SOUNDS = {
    "HIT_NORMAL": "hit_normal",
    "HIT_CRITICAL": "hit_critical",
    "EXPLOSION": "explosion",
    "DEFLECT": "deflect",
    "MISS": "miss",
}

# UI sounds (menu interactions, button clicks, etc.)
UI_SOUNDS = {
    "BUTTON_CLICK": "button_click",
    "BUTTON_HOVER": "button_hover",
    "MENU_OPEN": "menu_open",
    "MENU_CLOSE": "menu_close",
    "UNIT_SELECT": "unit_select",
    "INVALID_ACTION": "invalid_action",
    "TURN_START": "turn_start",
    "TURN_END": "turn_end",
}

# Music tracks
MUSIC_TRACKS = {
    "MAIN_MENU": "main_menu_theme",
    "BATTLE": "battle_theme",
    "VICTORY": "victory_theme",
    "DEFEAT": "defeat_theme",
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


def get_impact_sound(impact_type: str) -> str:
    """
    Get the sound key for an impact type.

    Args:
        impact_type: Impact type (e.g., "HIT_CRITICAL", "EXPLOSION")

    Returns:
        Sound key (filename without extension), or None if not found
    """
    return IMPACT_SOUNDS.get(impact_type.upper())


def get_ui_sound(ui_event: str) -> str:
    """
    Get the sound key for a UI event.

    Args:
        ui_event: UI event type (e.g., "BUTTON_CLICK", "UNIT_SELECT")

    Returns:
        Sound key (filename without extension), or None if not found
    """
    return UI_SOUNDS.get(ui_event.upper())


def get_music_track(track_name: str) -> str:
    """
    Get the sound key for a music track.

    Args:
        track_name: Track name (e.g., "MAIN_MENU", "BATTLE")

    Returns:
        Sound key (filename without extension), or None if not found
    """
    return MUSIC_TRACKS.get(track_name.upper())
