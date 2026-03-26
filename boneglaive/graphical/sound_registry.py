#!/usr/bin/env python3
"""
Sound Registry for Boneglaive
Maps skill names, actions, and events to sound files.
"""

# Sound registry: maps event/skill names to sound keys
# Sound keys are filenames (without .wav extension)
# The SoundManager will look for these in sounds/<category>/<sound_key>.wav

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
    "GRAE_EXCHANGE": "grae_exchange",
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

# Multi-event skill sounds (played within animations at specific moments)
# These are called directly by animations using play_sound() helper
MULTI_EVENT_SOUNDS = {
    # GLAIVEMAN - Judgement (3 events)
    "judgement_windup": "sounds/skills/judgement_windup.wav",   # Wind-up phase (optional)
    "judgement_throw": "sounds/skills/judgement_throw.wav",     # Glaive leaving hand
    "judgement_impact": "sounds/skills/judgement_impact.wav",   # Normal impact
    "judgement_critical": "sounds/skills/judgement_critical.wav", # Critical hit with lightning

    # GLAIVEMAN - Pry (3 events)
    "pry_lever": "sounds/skills/pry_lever.wav",       # Lever prying up
    "pry_ceiling": "sounds/skills/pry_ceiling.wav",   # Ceiling crash
    "pry_impact": "sounds/skills/pry_impact.wav",     # Ground explosion

    # GLAIVEMAN - Autoclave (2 events)
    "autoclave_ignition": "sounds/skills/autoclave_ignition.wav",  # Fire burst at center
    "autoclave_steam": "sounds/skills/autoclave_steam.wav",        # Steam jets expanding

    # GLAIVEMAN - Vault (4 events: base + upgraded variants)
    "vault_launch": "sounds/skills/vault_launch.wav",              # Leap off ground (base)
    "vault_launch_upgraded": "sounds/skills/vault_launch_upgraded.wav",  # Leap off ground (upgraded - double flip)
    "vault_land": "sounds/skills/vault_land.wav",                  # Landing impact (base)
    "vault_impact": "sounds/skills/vault_impact.wav",              # Landing impact (upgraded - AOE shockwave)

    # GLAIVEMAN - Glaive Sweep (3 events)
    "glaive_sweep_windup": "sounds/skills/glaive_sweep_windup.wav",  # Pulling back
    "glaive_sweep_swing": "sounds/skills/glaive_sweep_swing.wav",    # Circular arc
    "glaive_sweep_impact": "sounds/skills/glaive_sweep_impact.wav",  # Hits connecting

    # GLAIVEMAN - Basic Attack (3 events)
    "glaiveman_attack_windup": "sounds/skills/glaiveman_attack_windup.wav",  # Pull back polearm
    "glaiveman_attack_sweep": "sounds/skills/glaiveman_attack_sweep.wav",    # Blade whoosh
    "glaiveman_attack_impact": "sounds/skills/glaiveman_attack_impact.wav",  # Metal impact

    # MANDIBLE FOREMAN - Basic Attack (3 events)
    "mandible_attack_open": "sounds/skills/mandible_attack_open.wav",      # Jaws opening from 4 directions
    "mandible_attack_crush": "sounds/skills/mandible_attack_crush.wav",    # Jaws slamming shut
    "mandible_attack_release": "sounds/skills/mandible_attack_release.wav",  # Jaws releasing

    # MANDIBLE FOREMAN - Viseroy (4 events)
    "viseroy_snap": "sounds/skills/viseroy_snap.wav",          # Jaws snapping shut on victim
    "viseroy_grind": "sounds/skills/viseroy_grind.wav",        # Grinding/chewing motion
    "viseroy_clamp": "sounds/skills/viseroy_clamp.wav",        # Final hold/squeeze
    "viseroy_tick_squeeze": "sounds/skills/viseroy_tick_squeeze.wav",  # Periodic damage squeeze

    # MANDIBLE FOREMAN - Discharge (1 event)
    "discharge_spring": "sounds/skills/discharge_spring.wav",  # Jaws springing open to release

    # MANDIBLE FOREMAN - Site Inspection (2 events)
    "site_inspection_deploy": "sounds/skills/site_inspection_deploy.wav",  # Laser levels deploying
    "site_inspection_scan": "sounds/skills/site_inspection_scan.wav",      # Scanning sweep

    # MANDIBLE FOREMAN - Site Inspection Upgraded (2 events)
    "site_inspection_hologram": "sounds/skills/site_inspection_hologram.wav",  # Holographic projection
    "site_inspection_overlay": "sounds/skills/site_inspection_overlay.wav",    # Tactical overlay

    # MANDIBLE FOREMAN - Expedite (3 events)
    "expedite_charge": "sounds/skills/expedite_charge.wav",    # Steam pressure building
    "expedite_rush": "sounds/skills/expedite_rush.wav",        # High-speed charge
    "expedite_impact": "sounds/skills/expedite_impact.wav",    # Impact/stopping

    # MANDIBLE FOREMAN - Jawline (2 events)
    "jawline_deploy": "sounds/skills/jawline_deploy.wav",      # Bear traps sliding out on cables
    "jawline_snap": "sounds/skills/jawline_snap.wav",          # All 8 traps snapping shut

    # MANDIBLE FOREMAN - Jawline Upgraded (4 events)
    "jawline_upgraded_launch": "sounds/skills/jawline_upgraded_launch.wav",  # Ball of traps launching
    "jawline_upgraded_roll": "sounds/skills/jawline_upgraded_roll.wav",      # Rolling/rumbling
    "jawline_upgraded_deploy": "sounds/skills/jawline_upgraded_deploy.wav",  # Traps bursting outward
    "jawline_upgraded_snap": "sounds/skills/jawline_upgraded_snap.wav",      # Multiple traps snapping

    # MARROW CONDENSER - Ossify (3 events)
    "ossify_compression": "sounds/skills/ossify_compression.wav",    # Bone structure compressing inward
    "ossify_crystallize": "sounds/skills/ossify_crystallize.wav",    # Crystalline bone structure forming
    "ossify_harden": "sounds/skills/ossify_harden.wav",              # Final defensive shell hardening

    # MARROW CONDENSER - Bone Tithe (3 events)
    "bone_tithe_extraction": "sounds/skills/bone_tithe_extraction.wav",  # Tendrils shooting outward
    "bone_tithe_drain": "sounds/skills/bone_tithe_drain.wav",            # Marrow draining from enemies
    "bone_tithe_absorb": "sounds/skills/bone_tithe_absorb.wav",          # Marrow absorption with empowerment

    # MARROW CONDENSER - Marrow Dike (3 events)
    "marrow_dike_fracture": "sounds/skills/marrow_dike_fracture.wav",  # Ground cracking at wall positions
    "marrow_dike_erupt": "sounds/skills/marrow_dike_erupt.wav",        # Walls erupting from ground
    "marrow_dike_solidify": "sounds/skills/marrow_dike_solidify.wav",  # Walls hardening with network glow

    # MARROW CONDENSER - Bone Tithe Death Heal (upgraded passive, 3 events)
    "bone_tithe_death_explosion": "sounds/skills/bone_tithe_death_explosion.wav",    # Gore eruption on death
    "bone_tithe_death_distribute": "sounds/skills/bone_tithe_death_distribute.wav",  # Viscera flying to allies
    "bone_tithe_death_heal": "sounds/skills/bone_tithe_death_heal.wav",              # Allies absorbing marrow energy

    # MARROW CONDENSER - Basic Attack (3 events)
    "marrow_attack_gather": "sounds/skills/marrow_attack_gather.wav",    # Bone and marrow coalescing into ball
    "marrow_attack_launch": "sounds/skills/marrow_attack_launch.wav",    # Bone ball hurled toward target
    "marrow_attack_impact": "sounds/skills/marrow_attack_impact.wav",    # Bone and marrow explosion on impact

    # DELPHIC APPRAISER - Divine Depreciation (4 events)
    "divine_depreciation_fracture": "sounds/skills/divine_depreciation_fracture.wav",    # Reality fractures around target
    "divine_depreciation_collapse": "sounds/skills/divine_depreciation_collapse.wav",    # Value collapses into vortex
    "divine_depreciation_implosion": "sounds/skills/divine_depreciation_implosion.wav",  # Reality implodes with massive flash
    "divine_depreciation_reroll": "sounds/skills/divine_depreciation_reroll.wav",        # All furniture rerolls values

    # DELPHIC APPRAISER - Auction Curse (4 events)
    "auction_curse_podiums": "sounds/skills/auction_curse_podiums.wav",              # Podiums rise at furniture locations
    "auction_curse_manifestation": "sounds/skills/auction_curse_manifestation.wav",  # Ghostly auctioneers manifest
    "auction_curse_gavel_slam": "sounds/skills/auction_curse_gavel_slam.wav",        # Gavels slam in bidding frenzy
    "auction_curse_convergence": "sounds/skills/auction_curse_convergence.wav",      # Curse beams converge on target

    # DELPHIC APPRAISER - Market Futures (3 events)
    "market_futures_assessment": "sounds/skills/market_futures_assessment.wav",  # Golden scanner beams assess furniture
    "market_futures_rift": "sounds/skills/market_futures_rift.wav",              # Temporal rift opens
    "market_futures_anchor": "sounds/skills/market_futures_anchor.wav",          # Anchor manifests and embeds

    # DELPHIC APPRAISER - Parallax (Teleport) (3 events)
    "parallax_anchor_glow": "sounds/skills/parallax_anchor_glow.wav",        # Anchor glows with golden energy
    "parallax_dissolve": "sounds/skills/parallax_dissolve.wav",              # Unit dissolves into currency particles
    "parallax_rematerialize": "sounds/skills/parallax_rematerialize.wav",    # Particles converge and reform at destination

    # DELPHIC APPRAISER - Auction Curse Tick (3 events)
    "auction_curse_tick_seething": "sounds/skills/auction_curse_tick_seething.wav",        # Curse seethes around afflicted unit
    "auction_curse_tick_radiation": "sounds/skills/auction_curse_tick_radiation.wav",      # Curse radiates to furniture
    "auction_curse_tick_corruption": "sounds/skills/auction_curse_tick_corruption.wav",    # Furniture corrupted, values inflate

    # DELPHIC APPRAISER - Basic Attack (3 events)
    "delphic_attack_appraisal": "sounds/skills/delphic_attack_appraisal.wav",  # Astral appraisal - calculating value
    "delphic_attack_launch": "sounds/skills/delphic_attack_launch.wav",        # Launch astral bolt
    "delphic_attack_impact": "sounds/skills/delphic_attack_impact.wav",        # Astral value impact

    # DELPHIC APPRAISER - Deft(?) Reroll (2 events)
    "deft_reroll_activation": "sounds/skills/deft_reroll_activation.wav",  # Gold pulse activation
    "deft_reroll_spinning": "sounds/skills/deft_reroll_spinning.wav",      # Slot machine number cycling

    # DELPHIC APPRAISER - Auction Curse Soul Collection (3 events)
    "auction_soul_manifest": "sounds/skills/auction_soul_manifest.wav",      # Astral auctioneers rise at furniture positions
    "auction_soul_transfer": "sounds/skills/auction_soul_transfer.wav",      # Soul emerges from corpse and streams to auctioneers
    "auction_soul_descent": "sounds/skills/auction_soul_descent.wav",        # Auctioneers descend with the collected soul

    # INTERFERER - Basic Attack (2 events)
    "interferer_attack_windup_swing": "sounds/skills/interferer_attack_windup_swing.wav",  # Carabiners charging then dual whoosh through air
    "interferer_attack_impact": "sounds/skills/interferer_attack_impact.wav",              # Metallic impact with EM burst

    # INTERFERER - Neural Shunt (2 events)
    "neural_shunt_strike_converge": "sounds/skills/neural_shunt_strike_converge.wav",  # Carabiner strike into radio towers triangulating
    "neural_shunt_shock": "sounds/skills/neural_shunt_shock.wav",                      # Neural interference shock at target

    # INTERFERER - Karrier Rave phase-out (1 event)
    "karrier_rave_phaseout": "sounds/skills/karrier_rave_phaseout.wav",  # Static/tuning into carrier wave then phasing out of reality

    # INTERFERER - Karrier Rave triple strike (2 events)
    "karrier_rave_strike_hit": "sounds/skills/karrier_rave_strike_hit.wav",      # Each rapid carabiner strike impact (plays twice)
    "karrier_rave_strike_final": "sounds/skills/karrier_rave_strike_final.wav",  # Third strike - massive combined burst

    # INTERFERER - Scalar Node trigger (1 event)
    "scalar_node_trigger": "sounds/skills/scalar_node_trigger.wav",  # Standing wave erupts into searing blue-white electrical column

    # FOWL CONTRIVANCE - Parabol (2 events)
    "parabol_launch": "sounds/skills/parabol_launch.wav",        # Mortar fires - heavy thump of shell leaving cannon
    "parabol_impact": "sounds/skills/parabol_impact.wav",        # Massive shell detonates - central explosion + rippling splashes

    # FOWL CONTRIVANCE - Parabol Upgraded (2 additional events)
    "parabol_underground": "sounds/skills/parabol_underground.wav",       # Shell burrows underground - rumbling subsurface travel
    "parabol_second_impact": "sounds/skills/parabol_second_impact.wav",   # Cyan eruption from below - upward explosion from ground

    # FOWL CONTRIVANCE - Fragcrest (3 events, shared with trap variant)
    "fragcrest_detonate": "sounds/skills/fragcrest_detonate.wav",  # Claymore detonation - sharp directional blast
    "fragcrest_burst": "sounds/skills/fragcrest_burst.wav",        # Shrapnel cone releasing - metal shriek through the air
    "fragcrest_impact": "sounds/skills/fragcrest_impact.wav",      # Fragments embedding in targets

    # FOWL CONTRIVANCE - Gaussian Dusk charge (2 events)
    "gaussian_dusk_charge_start": "sounds/skills/gaussian_dusk_charge_start.wav",  # Rail gun beginning to charge - building electromagnetic hum
    "gaussian_dusk_charge_ready": "sounds/skills/gaussian_dusk_charge_ready.wav",  # Fully charged - intense high-pitched tone

    # FOWL CONTRIVANCE - Gaussian Dusk fire (1 event)
    "gaussian_dusk_fire": "sounds/skills/gaussian_dusk_fire.wav",  # Hypersonic rail projectile - massive crack/boom across the map

    # FOWL CONTRIVANCE - Rail Genesis death explosion (2 events)
    "rail_genesis_charge": "sounds/skills/rail_genesis_charge.wav",    # Rail network destabilizing - rising electrical whine across all rails
    "rail_genesis_detonate": "sounds/skills/rail_genesis_detonate.wav",  # Catastrophic chain detonation across entire rail network

    # FOWL CONTRIVANCE - Basic Attack (2 events)
    "fowl_attack_charge": "sounds/skills/fowl_attack_charge.wav",  # Brief EM charge-up before firing
    "fowl_attack_impact": "sounds/skills/fowl_attack_impact.wav",  # Electromagnetic bolt impact - cyan spark burst
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
