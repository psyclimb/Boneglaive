#!/usr/bin/env python3
"""
Animation Factory
Maps skill names to animation classes and creates appropriate animations.
"""
from typing import Optional, TYPE_CHECKING
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from boneglaive.graphical.animations.core import AnimatedUnit, TILE_SIZE
from boneglaive.graphical.animations.glaiveman import (
    LightningBolt, CrossBeam, AutoclaveAnimation, AutoclaveAnimationV2, SpinningGlaiveProjectile,
    PryImpactAnimation, VaultAnimationController, VaultAnimationControllerUpgraded,
    PryAnimation, JudgementAnimation, GlaiveSweepAnimation, AutoclaveFailureAnimation
)
from boneglaive.graphical.animations.mandible_foreman import (
    JawClamp, ViseroyTrap, ViseroyRelease, JawTighten, SiteInspectionBuff,
    SiteInspectionScan, SiteInspectionScanUpgraded, ExpediteRush, JawlineNetwork, JawlineNetworkUpgraded
)
from boneglaive.graphical.animations.potpourrist import (
    PedestalStrike, InfuseEffect, DemiluneSwing, GraniteGeasEffect,
    MelangeEminenceHealAnimation, MelangeEminenceInfusedHealAnimation
)
from boneglaive.graphical.animations.grayman import (
    DeltaConfigAnimation,
    GraeExchangeAnimation,
    EstrangeBeam,
    GraymanEchoDeathExplosionAnimation,
)
from boneglaive.graphical.animations.interferer import (
    NeutronIlluminantCardinal,
    NeutronIlluminantDiagonal,
    NeuralShuntAnimation,
    ScalarNodeTriggerAnimation,
    KarrierRavePhaseOut,
    KarrierRaveTripleStrike,
)
from boneglaive.graphical.animations.delphic_appraiser import (
    DivineDrepreciationAnimation,
    AuctionCurseAnimation,
    AuctionCurseTickAnimation,
    AuctionCurseSoulCollectionAnimation,
    MarketFuturesAnimation,
    MarketFuturesTeleportAnimation,
    DeftRerollAnimation,
)
from boneglaive.graphical.animations.marrow_condenser import (
    OssifyAnimation,
    BoneTitheAnimation,
    BoneTitheDeathHealAnimation,
    MarrowDikeAnimation,
    MarrowDikeWallDespawnAnimation,
)
from boneglaive.graphical.animations.derelictionist import (
    PartitionAnimation,
    PartitionHitAnimation,
    VagalRunAnimation,
    VagalRunAbreactionAnimation,
    DerelictPushTrail,
    DerelictBuildingFormation,
    DerelictBuildingTiles,
)
from boneglaive.graphical.animations.fowl_contrivance import (
    ParabolAnimation,
    ParabolAnimationUpgraded,
    FragcrestAnimation,
    FragcrestTrapAnimation,
    GaussianDuskFireAnimation,
    RailGenesisDeathExplosionAnimation,
)
from boneglaive.graphical.animations.gas_machinist import (
    VaporSpawnAnimation,
    DivergeAnimation,
    DivergeAnimationUpgraded,
    AerosolizeArmsAnimation,
    VaporAOETickAnimation,
)
from boneglaive.graphical.animations.core_animations import (
    RespawnAnimation,
)
from boneglaive.graphical.animations.landscaper import (
    HornswoggleAnimation,
    TopiaryBreathAnimation,
    DissonanceAnimation,
    SlagWallDespawnAnimation,
    TopiaryRevertAnimation,
)

from boneglaive.graphical.animations.ordnance_graft import (
    InoculantAnimation,
    DroneInoculantAnimation,
    SkyhookAnimationController,
    HarvestAnimation,
)

# Import sound system
from boneglaive.graphical.sound_registry import get_sound_for_skill
from boneglaive.graphical.sound_manager import get_sound_manager

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.graphical.camera import Camera


class AnimationFactory:
    """
    Factory for creating skill animations based on skill names.
    Maps skill names to their corresponding animation classes.
    Uses Camera system for coordinate conversion (resize-safe).
    """

    # Skill name → (animation_class, kwargs)
    SKILL_ANIMATIONS = {
        # GLAIVEMAN skills
        "JUDGEMENT": (JudgementAnimation, {}),  # New full animation: wind-up, flight, impact (lightning on crit)
        "PRY": (PryAnimation, {}),  # New full animation: pry up, ceiling impact, falling debris, ground explosion
        "VAULT": (VaultAnimationController, {}),  # Acrobatic leap with flip
        "VAULT_UPGRADED": (VaultAnimationControllerUpgraded, {}),  # Extended vault with double flip, higher arc, enhanced effects
        "AUTOCLAVE": (AutoclaveAnimationV2, {}),  # Enhanced: fire burst, steam cross, spinning glaives on every tile, healing
        "AUTOCLAVE_FAILURE": (AutoclaveFailureAnimation, {}),  # Failed Autoclave (no targets): shake, glow, steam, !?!?! symbols, fizzle
        "GLAIVE_SWEEP": (GlaiveSweepAnimation, {}),  # Circular sweep attack hitting all 8 adjacent tiles (upgraded Autoclave 2nd activation)

        # MANDIBLE FOREMAN skills
        "EXPEDITE": (ExpediteRush, {}),  # Discharge skill is named "Expedite"
        "DISCHARGE": (ViseroyRelease, {}),  # Release animation for Viseroy trap (when it ends)
        "SITE_INSPECTION": (SiteInspectionScan, {}),  # Laser scan animation
        "SITE_INSPECTION_UPGRADED": (SiteInspectionScanUpgraded, {}),  # Enhanced holographic scan with dual-pass analysis
        "JAWLINE": (JawlineNetwork, {}),  # Network of bear traps (3x3 around FOREMAN)
        "JAWLINE_UPGRADED": (JawlineNetworkUpgraded, {}),  # Directional cable spools with rolling traps (3x9 line)
        "VISEROY": (ViseroyTrap, {}),  # Passive (basic attack animation)
        "VISEROY_TICK": (JawTighten, {}),  # Trap tick damage animation

        # POTPOURRIST skills
        "PEDESTAL_STRIKE": (PedestalStrike, {}),
        "INFUSE": (InfuseEffect, {}),
        "DEMILUNE": (DemiluneSwing, {}),
        "DEMILUNE_INFUSED": (DemiluneSwing, {"infused": True}),
        "DEMILUNE_UPGRADED": (DemiluneSwing, {"upgraded": True}),
        "DEMILUNE_INFUSED_UPGRADED": (DemiluneSwing, {"infused": True, "upgraded": True}),
        "GRANITE_GEAS": (GraniteGeasEffect, {}),
        "MELANGE_EMINENCE_HEAL": (MelangeEminenceHealAnimation, {}),
        "MELANGE_EMINENCE_INFUSED_HEAL": (MelangeEminenceInfusedHealAnimation, {}),

        # GRAYMAN skills
        "DELTA_CONFIG": (DeltaConfigAnimation, {}),
        "ESTRANGE": (EstrangeBeam, {}),
        "GRAE_EXCHANGE": (GraeExchangeAnimation, {}),
        "GRÆ_EXCHANGE": (GraeExchangeAnimation, {}),  # Handle special character
        "GRAYMAN_ECHO_DEATH": (GraymanEchoDeathExplosionAnimation, {}),

        # MARROW CONDENSER skills
        "OSSIFY": (OssifyAnimation, {}),
        "MARROW_DIKE": (MarrowDikeAnimation, {}),
        "BONE_TITHE": (BoneTitheAnimation, {}),
        "BONE_TITHE_DEATH_HEAL": (BoneTitheDeathHealAnimation, {}),
        "MARROW_DIKE_WALL_DESPAWN": (MarrowDikeWallDespawnAnimation, {}),

        # FOWL CONTRIVANCE skills
        "GAUSSIAN_DUSK": (GaussianDuskFireAnimation, {}),  # Rail gun firing (fires immediately)
        "BIG_ARC": (ParabolAnimation, {}),  # Mortar barrage (skill name is Parabol)
        "PARABOL": (ParabolAnimation, {}),  # Alternative name
        "FRAGCREST": (FragcrestAnimation, {}),  # Directional fragmentation cone
        "RAIL_GENESIS_DEATH_EXPLOSION": (RailGenesisDeathExplosionAnimation, {}),  # Death explosion

        # GAS MACHINIST skills
        "BROACHING_GAS": (VaporSpawnAnimation, {"vapor_type": "BROACHING"}),
        "SAFT_E_GAS": (VaporSpawnAnimation, {"vapor_type": "SAFETY"}),
        "COOLANT_GAS": (VaporSpawnAnimation, {"vapor_type": "COOLANT"}),
        "CUTTING_GAS": (VaporSpawnAnimation, {"vapor_type": "CUTTING"}),
        "CALIBRATION_GAS": (VaporSpawnAnimation, {"vapor_type": "CALIBRATION"}),
        "LIVING_AEROSOL_GAS": (VaporSpawnAnimation, {"vapor_type": "LIVING_AEROSOL"}),
        "DIVERGE": (DivergeAnimation, {}),  # Splits target into Coolant and Cutting vapors
        "AEROSOLIZE_ARMS": (AerosolizeArmsAnimation, {}),  # Disarms target and creates Living Aerosol
        # Vapor AOE tick effects
        "VAPOR_AOE_BROACHING": (VaporAOETickAnimation, {"vapor_type": "BROACHING"}),
        "VAPOR_AOE_SAFETY": (VaporAOETickAnimation, {"vapor_type": "SAFETY"}),
        "VAPOR_AOE_COOLANT": (VaporAOETickAnimation, {"vapor_type": "COOLANT"}),
        "VAPOR_AOE_CUTTING": (VaporAOETickAnimation, {"vapor_type": "CUTTING"}),
        "VAPOR_AOE_CALIBRATION": (VaporAOETickAnimation, {"vapor_type": "CALIBRATION"}),

        # DELPHIC APPRAISER skills
        "MARKET_FUTURES": (MarketFuturesAnimation, {}),
        "AUCTION_CURSE": (AuctionCurseAnimation, {}),
        "AUCTION_CURSE_TICK": (AuctionCurseTickAnimation, {}),
        "AUCTION_CURSE_SOUL_COLLECTION": (AuctionCurseSoulCollectionAnimation, {}),
        "DIVINE_DEPRECIATION": (DivineDrepreciationAnimation, {}),
        "DEFT(?) REROLL": (DeftRerollAnimation, {}),
        "DEFT(?)_REROLL": (DeftRerollAnimation, {}),  # Normalized version (space → underscore)
        "DEFT_REROLL": (DeftRerollAnimation, {}),  # Fallback if converted with underscores
        "PARALLAX": (MarketFuturesTeleportAnimation, {}),

        # INTERFERER skills
        "NEUTRON_ILLUMINANT_CARDINAL": (NeutronIlluminantCardinal, {}),
        "NEUTRON_ILLUMINANT_DIAGONAL": (NeutronIlluminantDiagonal, {}),
        "NEURAL_SHUNT": (NeuralShuntAnimation, {}),
        "KARRIER_RAVE": (KarrierRavePhaseOut, {}),
        "KARRIER_RAVE_STRIKE": (KarrierRaveTripleStrike, {}),  # Triple melee attack
        "SCALAR_NODE": (None, {}),  # Trap placement (no animation - silent)

        # DERELICTIONIST skills
        "VAGAL_RUN": (VagalRunAnimation, {}),
        "VAGAL_RUN_ABREACTION": (VagalRunAbreactionAnimation, {}),  # Delayed effect (no connection arc)
        "PARTITION": (PartitionAnimation, {}),
        "DERELICT_PUSH_TRAIL": (DerelictPushTrail, {}),  # Push trail for base Derelict skill
        "DERELICT_BUILDING_FORMATION": (DerelictBuildingFormation, {}),  # Dust cloud animation
        "DERELICT_BUILDING_TILES": (DerelictBuildingTiles, {}),  # Persistent building tiles

        # LANDSCAPER skills
        "HORNSWOGGLE": (HornswoggleAnimation, {}),
        "TOPIARY_BREATH": (TopiaryBreathAnimation, {}),
        "DISSONANCE": (DissonanceAnimation, {}),
        "SLAG_WALL_DESPAWN": (SlagWallDespawnAnimation, {}),
        "TOPIARY_REVERT": (TopiaryRevertAnimation, {}),

        # ORDNANCE GRAFT skills
        "INOCULANT": (InoculantAnimation, {}),
        "SKYHOOK": (SkyhookAnimationController, {}),  # Vault-style: moves the caster sprite
        "HARVEST": (HarvestAnimation, {}),

        # Core game events
        "RESPAWN": (RespawnAnimation, {}),
    }

    @classmethod
    def create_animation(cls, skill_name: str, caster_unit: AnimatedUnit,
                        target_unit: Optional[AnimatedUnit] = None,
                        target_pos: Optional[tuple] = None,
                        is_crit: bool = False,
                        is_infused: bool = False,
                        particle_emitter = None,
                        debris_list = None,
                        screen_shake_callback = None,
                        screen_flash_callback = None,
                        units_list = None,
                        damage_callback = None,
                        camera = None,
                        game = None,
                        bounce_count: int = 2,
                        trajectory = None,
                        reflected_skill_name: str = None,
                        zone_tiles = None,
                        building_tiles = None,
                        **kwargs):
        """
        Create an animation for a skill.

        Args:
            skill_name: Name of the skill (e.g., "JUDGEMENT", "PRY")
            caster_unit: Visual unit casting the skill
            target_unit: Visual unit being targeted (optional)
            target_pos: Target grid position (grid_x, grid_y) (optional)

        Returns:
            Animation instance, or None if no animation defined
        """
        # Normalize skill name (remove spaces and hyphens, uppercase)
        skill_key = skill_name.upper().replace(" ", "_").replace("-", "_")

        # Gaussian Dusk animations are now differentiated by skill name at event creation
        # "Gaussian Dusk Charge" -> GAUSSIAN_DUSK_CHARGE
        # "Gaussian Dusk Fire" -> GAUSSIAN_DUSK_FIRE
        # No state checking needed here anymore

        # Check for Fragcrest trap mode (override class before lookup)
        if skill_key == "FRAGCREST" and kwargs.get('is_trap', False):
            anim_data = (FragcrestTrapAnimation, {})
        else:
            # Get animation class and kwargs from registry
            anim_data = cls.SKILL_ANIMATIONS.get(skill_key)

        if not anim_data:
            return None

        anim_class, base_kwargs = anim_data

        if anim_class is None:
            return None

        # Play skill sound effect
        sound_key = get_sound_for_skill(skill_name)
        if sound_key:
            try:
                sound_manager = get_sound_manager()
                sound_manager.play(sound_key, category="skills")
            except Exception as e:
                # Don't crash if sound fails - just log it
                pass

        # Prepare animation kwargs
        # Merge base_kwargs with passed-in kwargs (preserving custom parameters like start_pos, end_pos)
        merged_kwargs = base_kwargs.copy()
        merged_kwargs.update(kwargs)  # Add any custom kwargs passed in
        merged_kwargs['game'] = game  # Add game instance to kwargs
        merged_kwargs['bounce_count'] = bounce_count  # Add bounce count for Matador animation
        kwargs = merged_kwargs

        # Use camera for coordinate conversion (if provided)
        # Falls back to default offsets for backwards compatibility
        if camera:
            grid_to_screen = camera.grid_to_screen
        else:
            # Fallback for older code that doesn't pass camera
            from boneglaive.graphical.animations.core import TILE_SIZE as DEFAULT_TILE_SIZE
            GRID_OFFSET_X = 100
            GRID_OFFSET_Y = 50
            def grid_to_screen(grid_x, grid_y, centered=True):
                """Fallback grid-to-screen conversion."""
                screen_x = GRID_OFFSET_X + grid_x * DEFAULT_TILE_SIZE
                screen_y = GRID_OFFSET_Y + grid_y * DEFAULT_TILE_SIZE
                if centered:
                    screen_x += DEFAULT_TILE_SIZE // 2
                    screen_y += DEFAULT_TILE_SIZE // 2
                return screen_x, screen_y

        # Determine target based on animation type
        if target_unit:
            target_x, target_y = grid_to_screen(target_unit.grid_x, target_unit.grid_y)
            kwargs['target_x'] = target_x
            kwargs['target_y'] = target_y
        elif target_pos:
            # NOTE: target_pos is (grid_y, grid_x) format from renderer
            # Convert grid to screen: target_pos[1] is grid_x, target_pos[0] is grid_y
            target_x, target_y = grid_to_screen(target_pos[1], target_pos[0])
            kwargs['target_x'] = target_x
            kwargs['target_y'] = target_y
        else:
            # Some skills target self or area
            if caster_unit:
                target_x, target_y = grid_to_screen(caster_unit.grid_x, caster_unit.grid_y)
                kwargs['target_x'] = target_x
                kwargs['target_y'] = target_y
            else:
                # No caster and no target position - cannot determine location
                kwargs['target_x'] = 0
                kwargs['target_y'] = 0

        # Create animation instance
        # Different animations have different constructor signatures
        try:
            # Convert caster grid coords to screen coords (if caster exists)
            if caster_unit:
                # Use game unit's position if available (post-move), otherwise use AnimatedUnit's position
                if hasattr(caster_unit, 'game_unit') and caster_unit.game_unit:
                    # Use game unit's actual position (post-move)
                    caster_grid_x = caster_unit.game_unit.x
                    caster_grid_y = caster_unit.game_unit.y
                else:
                    # Fall back to AnimatedUnit's position
                    caster_grid_x = caster_unit.grid_x
                    caster_grid_y = caster_unit.grid_y

                caster_screen_x, caster_screen_y = grid_to_screen(caster_grid_x, caster_grid_y)
            else:
                # No caster (e.g., caster died before delayed effect like abreaction)
                # Use target position as fallback
                caster_screen_x, caster_screen_y = kwargs.get('target_x', 0), kwargs.get('target_y', 0)

            # Most animations expect target_x, target_y (or center_x, center_y)
            # JudgementAnimation - New full animation with wind-up, flight, and impact (lightning on crit)
            if anim_class.__name__ == "JudgementAnimation":
                # Requires: target_pos, game instance, camera, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            # SpinningGlaiveProjectile expects start_x, start_y, target_x, target_y, is_crit (legacy)
            elif anim_class.__name__ == "SpinningGlaiveProjectile":
                animation = anim_class(
                    start_x=caster_screen_x,
                    start_y=caster_screen_y,
                    target_x=kwargs.get('target_x', caster_screen_x),
                    target_y=kwargs.get('target_y', caster_screen_y),
                    is_crit=is_crit
                )
            elif anim_class.__name__ == "CrossBeam":
                # CrossBeam expects center_x, center_y, direction
                animation = anim_class(
                    center_x=caster_screen_x,
                    center_y=caster_screen_y,
                    direction=0
                )
            elif anim_class.__name__ == "AutoclaveAnimation":
                # AutoclaveAnimation creates all 4 beams at caster position (legacy)
                animation = anim_class(
                    center_x=caster_screen_x,
                    center_y=caster_screen_y,
                    max_range=3  # Autoclave has range 3
                )
            elif anim_class.__name__ == "AutoclaveAnimationV2":
                # AutoclaveAnimationV2 - Enhanced version with fire burst, glaives on every tile, healing
                # Requires: caster_unit, game instance, camera, standard callbacks
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,  # Passive AOE around caster
                    target_pos=(caster_unit.grid_y, caster_unit.grid_x) if caster_unit else None,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "PryAnimation":
                # PryAnimation - New full animation with ceiling impact and falling debris
                # Requires: target_pos, game instance, camera, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "VaultAnimationController":
                # VaultAnimationController needs target position
                if not target_pos:
                    return None

                # Check if vault was displaced (collision with ally move)
                actual_target_pos = target_pos
                if caster_unit and hasattr(caster_unit, 'game_unit') and hasattr(caster_unit.game_unit, 'vault_displaced_to'):
                    actual_target_pos = caster_unit.game_unit.vault_displaced_to
                    # Clear the flag
                    del caster_unit.game_unit.vault_displaced_to

                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=actual_target_pos,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    camera=camera
                )
            elif anim_class.__name__ == "SkyhookAnimationController":
                # ORDNANCE GRAFT Skyhook - Vault-style: moves the caster sprite along the
                # extraction arc. Needs the landing position + units_list so it can hide
                # the drone (it's carrying him) and reveal it at the landing.
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    camera=camera,
                    units_list=units_list
                )
            elif anim_class.__name__ == "VaultAnimationControllerUpgraded":
                # VaultAnimationControllerUpgraded needs target position (same signature as regular Vault)
                if not target_pos:
                    return None

                # Check if vault was displaced (collision with ally move)
                actual_target_pos = target_pos
                if caster_unit and hasattr(caster_unit, 'game_unit') and hasattr(caster_unit.game_unit, 'vault_displaced_to'):
                    actual_target_pos = caster_unit.game_unit.vault_displaced_to
                    # Clear the flag
                    del caster_unit.game_unit.vault_displaced_to

                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=actual_target_pos,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    camera=camera
                )
            elif anim_class.__name__ == "EstrangeBeam":
                # EstrangeBeam needs source, target, and particle emitter
                animation = anim_class(
                    source_x=caster_screen_x,
                    source_y=caster_screen_y,
                    target_x=kwargs['target_x'],
                    target_y=kwargs['target_y'],
                    particle_emitter=particle_emitter
                )
            elif anim_class.__name__ == "DeltaConfigAnimation":
                # DeltaConfigAnimation needs caster unit, target position, and particle emitter
                # Also needs game and units_list for upgraded abduction mechanics
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    particle_emitter=particle_emitter,
                    camera=camera,
                    game=kwargs.get('game'),
                    units_list=units_list if units_list else []
                )
            elif anim_class.__name__ == "GraeExchangeAnimation":
                # GraeExchangeAnimation needs caster unit, target position, and particle emitter
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    particle_emitter=particle_emitter,
                    camera=camera
                )
            elif anim_class.__name__ == "GraymanEchoDeathExplosionAnimation":
                # GRAYMAN DOPPELGANGER death explosion - psychic explosion affecting 3x3 area
                # Requires: caster_unit (dead doppelganger), camera, standard callbacks
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,
                    target_pos=(caster_unit.grid_y, caster_unit.grid_x) if caster_unit else target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=None,  # NO screen flash
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "InfuseEffect":
                # InfuseEffect needs caster position and caster unit
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    caster_unit=caster_unit
                )
            elif anim_class.__name__ == "DemiluneSwing":
                # DemiluneSwing needs caster, target positions, infused and upgraded flags
                # Use the is_infused parameter passed from the event (captured before skill execution)
                # Upgraded flag comes from default_kwargs in the animation map entry
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    caster_unit=caster_unit,
                    target_x=kwargs.get('target_x', caster_screen_x),
                    target_y=kwargs.get('target_y', caster_screen_y),
                    infused=is_infused,  # Use the parameter, not the game state
                    upgraded=base_kwargs.get('upgraded', False),  # Selenic Backdraft
                    targets=units_list,  # Pass all units so animation can detect hits
                    # Pass grid positions for accurate arc calculation
                    caster_grid_pos=(caster_unit.grid_y, caster_unit.grid_x) if hasattr(caster_unit, 'grid_y') else None,
                    target_grid_pos=target_pos,
                    camera=camera
                )
            elif anim_class.__name__ == "GraniteGeasEffect":
                # GraniteGeasEffect needs target position and target unit
                if not target_unit:
                    return None
                animation = anim_class(
                    target_x=kwargs['target_x'],
                    target_y=kwargs['target_y'],
                    target_unit=target_unit,
                    infused=is_infused  # Use the parameter from event
                )
            elif anim_class.__name__ in ["MelangeEminenceHealAnimation", "MelangeEminenceInfusedHealAnimation"]:
                # Melange Eminence passive healing animations
                # Requires: target_pos (POTPOURRIST position), camera, heal_amount from event
                if not target_pos:
                    return None

                # Get heal_amount from kwargs (passed from animation event)
                heal_amount = kwargs.get('heal_amount', 1 if anim_class.__name__ == "MelangeEminenceHealAnimation" else 2)

                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,  # POTPOURRIST position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game'),
                    heal_amount=heal_amount
                )
            elif anim_class.__name__ in ["NeutronIlluminantCardinal", "NeutronIlluminantDiagonal"]:
                # Radio Effulgent animations need caster position, particle emitter, and screen flash callback
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    caster_unit=caster_unit,
                    particle_emitter=particle_emitter,
                    screen_flash_callback=screen_flash_callback
                )
            elif anim_class.__name__ == "NeuralShuntAnimation":
                # Neural Shunt needs caster, target positions, and callbacks
                if not target_unit:
                    return None
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    target_x=kwargs.get('target_x', caster_screen_x),
                    target_y=kwargs.get('target_y', caster_screen_y),
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    particle_emitter=particle_emitter,
                    screen_flash_callback=screen_flash_callback,
                    screen_shake_callback=screen_shake_callback
                )
            elif anim_class.__name__ == "KarrierRavePhaseOut":
                # Karrier Rave phase-out (self-buff)
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    caster_unit=caster_unit,
                    particle_emitter=particle_emitter,
                    screen_flash_callback=screen_flash_callback
                )
            elif anim_class.__name__ == "KarrierRaveTripleStrike":
                # Karrier Rave triple strike (melee attack with Radio Effulgent patterns)
                if not target_unit:
                    return None
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    target_x=kwargs.get('target_x', caster_screen_x),
                    target_y=kwargs.get('target_y', caster_screen_y),
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    particle_emitter=particle_emitter,
                    screen_flash_callback=screen_flash_callback
                )
            elif anim_class.__name__ in ["SiteInspectionScan", "SiteInspectionScanUpgraded"]:
                # Site Inspection scan animation - needs center position (target_pos)
                # NOTE: target_pos is (grid_y, grid_x) format from renderer
                # Target position is where the scan is centered
                if target_pos:
                    # Convert grid to screen: target_pos[1] is grid_x, target_pos[0] is grid_y
                    center_x, center_y = grid_to_screen(target_pos[1], target_pos[0])
                else:
                    center_x, center_y = kwargs.get('target_x', caster_screen_x), kwargs.get('target_y', caster_screen_y)
                animation = anim_class(
                    center_x=center_x,
                    center_y=center_y,
                    camera=camera
                )
            elif anim_class.__name__ in ["JawlineNetwork", "JawlineNetworkUpgraded"]:
                # Jawline network - base version deploys from caster, upgraded needs target
                if anim_class.__name__ == "JawlineNetworkUpgraded":
                    # Upgraded version needs target position for direction
                    if not target_pos:
                        return None
                    # Convert grid to screen: target_pos[1] is grid_x, target_pos[0] is grid_y
                    target_x, target_y = grid_to_screen(target_pos[1], target_pos[0])
                    animation = anim_class(
                        center_x=caster_screen_x,
                        center_y=caster_screen_y,
                        target_x=target_x,
                        target_y=target_y,
                        camera=camera,
                        game=kwargs.get('game'),
                        caster_unit=caster_unit
                    )
                else:
                    # Base version - 3x3 around caster
                    animation = anim_class(
                        center_x=caster_screen_x,
                        center_y=caster_screen_y,
                        camera=camera
                    )
            elif anim_class.__name__ == "ExpediteRush":
                # Expedite rush - needs start, target, and caster unit
                # NOTE: target_pos is (grid_y, grid_x) format from renderer
                if not target_pos:
                    return None

                # IMPORTANT: Check if the foreman had a planned move that was cleared
                # If expedite_planned_start exists, use that as the starting position
                # First check kwargs (captured during pre-execution sync), then fall back to game_unit
                expedite_planned_start = kwargs.get('expedite_planned_start')
                if not expedite_planned_start:
                    # Fall back to checking game_unit directly (for backward compatibility)
                    if caster_unit and hasattr(caster_unit, 'game_unit') and caster_unit.game_unit:
                        game_unit = caster_unit.game_unit
                        if hasattr(game_unit, 'expedite_planned_start'):
                            expedite_planned_start = game_unit.expedite_planned_start

                if expedite_planned_start:
                    # Use the planned position as start
                    planned_y, planned_x = expedite_planned_start
                    caster_screen_x, caster_screen_y = grid_to_screen(planned_x, planned_y)

                # Convert grid to screen: target_pos[1] is grid_x, target_pos[0] is grid_y
                target_x, target_y = grid_to_screen(target_pos[1], target_pos[0])
                animation = anim_class(
                    start_x=caster_screen_x,
                    start_y=caster_screen_y,
                    target_x=target_x,
                    target_y=target_y,
                    foreman_unit=caster_unit,
                    target_grid_pos=target_pos,  # Pass grid position for final update
                    camera=camera,
                    target_unit=target_unit  # Pass target unit for impact effects
                )
            elif anim_class.__name__ in ["ViseroyTrap", "ViseroyRelease"]:
                # Viseroy animations - target coordinates
                animation = anim_class(
                    target_x=kwargs.get('target_x', caster_screen_x),
                    target_y=kwargs.get('target_y', caster_screen_y)
                )
            elif anim_class.__name__ == "DivineDrepreciationAnimation":
                # Divine Depreciation - reality-warping furniture reappraisal
                # Requires: target_pos (furniture position), all standard callbacks, game instance
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],  # Not used but required by signature
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Pass game instance for furniture detection
                )
            elif anim_class.__name__ == "AuctionCurseAnimation":
                # Auction Curse - cursed auction with furniture detection
                # Requires: target_pos (enemy unit), game instance for furniture within 2 tiles
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Pass game instance for furniture detection
                )
            elif anim_class.__name__ == "MarketFuturesAnimation":
                # Market Futures - temporal investment energy infusion
                # Requires: target_pos (furniture position), all standard callbacks, game instance
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],  # Not used but required by signature
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Pass game instance if needed
                )
            elif anim_class.__name__ == "MarketFuturesTeleportAnimation":
                # Parallax - Market Futures teleportation animation
                # Requires: target_pos (destination), camera, game instance, standard callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "DeftRerollAnimation":
                # Deft(?) Reroll - reroll furniture values in Divine Depreciation area
                # Requires: caster unit, game instance (for distortion), camera, callbacks
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,  # Self-targeting
                    target_pos=(caster_unit.grid_y, caster_unit.grid_x) if caster_unit else (0, 0),
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "OssifyAnimation":
                # Ossify - self-buff defensive compression animation
                # Requires: caster unit, standard callbacks
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,  # Self-targeting
                    target_pos=(caster_unit.grid_y, caster_unit.grid_x),  # Caster position
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "BoneTitheAnimation":
                # Bone Tithe - AOE life drain from enemies in 5x5 beam pattern
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,
                    target_pos=(caster_unit.grid_y, caster_unit.grid_x),
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "BoneTitheDeathHealAnimation":
                # Requires: death_pos, affected_allies from event kwargs
                death_pos = kwargs.get('death_pos')
                affected_allies = kwargs.get('affected_allies', [])
                heal_amount = kwargs.get('heal_amount', 0)

                if not death_pos or not affected_allies:
                    return None

                animation = anim_class(
                    death_pos=death_pos,
                    affected_allies=affected_allies,
                    heal_amount=heal_amount,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    camera=camera
                )
            elif anim_class.__name__ == "MarrowDikeAnimation":
                # Marrow Dike - 5x5 perimeter wall eruption animation
                # Requires: caster unit, game (for wall positions), camera, standard callbacks
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,  # Self-targeting (walls around caster)
                    target_pos=(caster_unit.grid_y, caster_unit.grid_x),  # Caster position
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Required for wall position calculation
                )

            elif anim_class.__name__ == "MarrowDikeWallDespawnAnimation":
                # Marrow Dike Wall Despawn - individual wall crumbling animation
                # Requires: target_pos (wall position), camera, standard callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,
                    target_pos=target_pos,  # Wall position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "PartitionAnimation":
                # Partition - protective barrier around ally
                # Requires: target_unit (ally), target_pos, camera, standard callbacks
                if not target_unit:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,  # Ally position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "VagalRunAnimation":
                # Vagal Run - lightning trauma therapy cascading down vagus nerve
                # Requires: target_unit (ally), target_pos, camera, standard callbacks
                if not target_unit:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,  # Ally position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "VagalRunAbreactionAnimation":
                # Vagal Run Abreaction - abreaction trigger (NO connection arc to caster)
                # Same nerve cascade effect, but starts immediately on target
                # Requires: target_unit, target_pos, camera, standard callbacks
                # NOTE: caster_unit may be None if DERELICTIONIST died
                if not target_unit:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,  # May be None
                    target_unit=target_unit,
                    target_pos=target_pos,  # Target position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "DerelictPushTrail":
                # Derelict push trail - Blue particle trail showing ally push displacement
                # Requires: start_pos, end_pos (grid coordinates), camera
                start_pos = kwargs.get('start_pos')
                end_pos = kwargs.get('end_pos')

                if not start_pos or not end_pos:
                    return None

                animation = anim_class(
                    start_pos=start_pos,
                    end_pos=end_pos,
                    camera=camera
                )
            elif anim_class.__name__ == "DerelictBuildingFormation":
                # Derelict building formation - Dust cloud when buildings form
                # Requires: building_tiles (list of grid positions), camera, game
                building_tiles = kwargs.get('building_tiles')

                if not building_tiles:
                    return None

                animation = anim_class(
                    building_tiles=building_tiles,
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ == "DerelictBuildingTiles":
                # Derelict building tiles - Persistent weathered wall effect
                # Requires: building_tiles (list of grid positions), camera, game
                building_tiles = kwargs.get('building_tiles')

                if not building_tiles:
                    return None

                animation = anim_class(
                    building_tiles=building_tiles,
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ == "ParabolAnimation":
                # Parabol - 3x3 mortar barrage with indirect fire
                # Check if skill is upgraded (uses underground parabola with second explosion)
                # Requires: target_pos (center of 3x3 area), camera, callbacks
                if not target_pos:
                    return None

                # Check for upgrade
                is_upgraded = False
                game = kwargs.get('game')
                if game and hasattr(caster_unit, 'game_unit') and caster_unit.game_unit:
                    from boneglaive.game.upgrades import UpgradeManager
                    is_upgraded = UpgradeManager.is_skill_upgraded(caster_unit.game_unit, "Parabol")

                # Use upgraded animation if skill is upgraded
                if is_upgraded:
                    animation = ParabolAnimationUpgraded(
                        caster_unit=caster_unit,
                        target_unit=None,  # Area attack, no specific target unit
                        target_pos=target_pos,  # Center of 3x3 area (grid_y, grid_x)
                        is_crit=is_crit,
                        is_infused=is_infused,
                        particle_emitter=particle_emitter,
                        debris_list=[],
                        screen_shake_callback=screen_shake_callback,
                        screen_flash_callback=screen_flash_callback,
                        units_list=units_list if units_list else [],
                        camera=camera,
                        game=game
                    )
                else:
                    animation = anim_class(
                        caster_unit=caster_unit,
                        target_unit=None,  # Area attack, no specific target unit
                        target_pos=target_pos,  # Center of 3x3 area (grid_y, grid_x)
                        is_crit=is_crit,
                        is_infused=is_infused,
                        particle_emitter=particle_emitter,
                        debris_list=[],
                        screen_shake_callback=screen_shake_callback,
                        screen_flash_callback=screen_flash_callback,
                        units_list=units_list if units_list else [],
                        camera=camera,
                        game=game
                    )
            elif anim_class.__name__ in ["FragcrestAnimation", "FragcrestTrapAnimation"]:
                # Fragcrest - directional fragmentation cone with knockback
                # Requires: target_pos (primary target), target_unit, camera, callbacks, game
                # FragcrestAnimation = normal cast, FragcrestTrapAnimation = trap detonation
                if not target_pos:
                    return None
                if not target_unit:
                    return None

                # Both animation classes use the same constructor
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=game,
                    is_trap=kwargs.get('is_trap', False),
                    trap_cone_positions=kwargs.get('trap_cone_positions', None)
                )
            elif anim_class.__name__ == "GaussianDuskFireAnimation":
                # Gaussian Dusk Fire - rail gun beam firing across map
                # Requires: caster_unit, target_pos (direction vector), camera, callbacks, game
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,  # This is actually the direction vector (dy, dx)!
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,  # Critical for clearing dimming!
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Required for calculating firing line
                )
            elif anim_class.__name__ == "RailGenesisDeathExplosionAnimation":
                # Rail Genesis death explosion - rail network detonation when FOWL CONTRIVANCE dies
                # Requires: caster_unit (dead FOWL CONTRIVANCE), game (for rail positions), camera, callbacks
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,
                    target_pos=None,  # Not needed, uses all rail positions from game
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Required for getting rail positions
                )
            elif anim_class.__name__ == "VaporSpawnAnimation":
                # Vapor spawn animation - needs target position and vapor type from kwargs
                animation = anim_class(
                    target_x=kwargs.get('target_x', 0),
                    target_y=kwargs.get('target_y', 0),
                    vapor_type=kwargs.get('vapor_type', 'BROACHING'),
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback
                )
            elif anim_class.__name__ == "DivergeAnimation":
                # Diverge - splits target into two or three specialized vapors
                # Check if Diverge is upgraded (creates 3 vapors)
                # Requires target_pos (position of unit/vapor being split), game instance
                if not target_pos:
                    return None

                # Check if skill is upgraded
                is_upgraded = False
                if caster_unit and hasattr(caster_unit, 'game_unit'):
                    game_unit = caster_unit.game_unit
                    if hasattr(game_unit, 'upgraded_skills') and 'Diverge' in game_unit.upgraded_skills:
                        is_upgraded = True
                elif caster_unit and hasattr(caster_unit, 'upgraded_skills'):
                    if 'Diverge' in caster_unit.upgraded_skills:
                        is_upgraded = True

                # Use upgraded animation if skill is upgraded
                anim_class_to_use = DivergeAnimationUpgraded if is_upgraded else anim_class

                animation = anim_class_to_use(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "VaporAOETickAnimation":
                # Vapor AOE tick - pulsing effect when vapor applies area effects
                animation = anim_class(
                    target_x=kwargs.get('target_x', 0),
                    target_y=kwargs.get('target_y', 0),
                    vapor_type=kwargs.get('vapor_type', 'BROACHING'),
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback
                )
            elif anim_class.__name__ == "AerosolizeArmsAnimation":
                # Aerosolize Arms - disarms target and creates Living Aerosol
                # Requires: caster_unit, target_unit, target_pos, game, camera, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "AuctionCurseTickAnimation":
                # Auction Curse Tick - periodic DOT damage with furniture inflation
                # Requires: target_pos (cursed unit position), game (for furniture), camera, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,  # Cursed unit position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Required for finding nearby furniture
                )
            elif anim_class.__name__ == "AuctionCurseSoulCollectionAnimation":
                # Auction Curse Soul Collection - death animation for upgraded Auction Curse (perfect timing)
                # Requires: caster_unit, target_unit (dying), target_pos, game (for furniture), camera, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,  # Dying cursed unit position (grid_y, grid_x)
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')  # Required for finding nearby furniture
                )
            elif anim_class.__name__ == "MatadorAnimation":
                # Matador - MASSIVE pelota projectile with multi-bounce ricochet
                # Requires: caster_unit, target_pos, camera, particle_emitter, game, bounce_count
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    camera=camera,
                    particle_emitter=particle_emitter,
                    game=kwargs.get('game'),
                    bounce_count=kwargs.get('bounce_count', 2)
                )
            elif anim_class.__name__ == "PoachAnimation":
                # Poach - Medium pelota with ricochet and buff stealing
                # Requires: caster_unit, target_pos, camera, particle_emitter, game, screen shake/flash
                if not target_pos:
                    return None

                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    camera=camera,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "BackhandAnimation":
                # Backhand - Self-buff stance animation
                # Requires: full standard signature (self-buff uses caster position as target)
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,  # None for self-buff
                    target_pos=target_pos if target_pos else (caster_unit.grid_y, caster_unit.grid_x),
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=debris_list if debris_list else [],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ == "BackhandReflectionAnimation":
                # Backhand Reflection - Reflected skill projectile animation
                # Requires: caster, target_pos (not used), camera, particle_emitter, callbacks, game
                # Plus: trajectory (list of positions), reflected_skill_name (reflected skill), bounce_count, is_infused, is_crit
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos if target_pos else (0, 0),  # Not used
                    camera=camera,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    game=game,
                    trajectory=trajectory if trajectory else [],
                    skill_name=reflected_skill_name if reflected_skill_name else 'Estrange',
                    bounce_count=bounce_count,
                    is_infused=is_infused,
                    is_crit=is_crit
                )
            elif anim_class.__name__ == "DerelictBuildingFormation":
                # Derelict Building Formation - Building rising animation
                # Requires: building_tiles (list of grid positions), camera, game
                if not building_tiles:
                    return None

                animation = anim_class(
                    building_tiles=building_tiles,
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ == "DerelictBuildingTiles":
                # Derelict Building Tiles - Persistent building tile effect
                # Requires: building_tiles (list of grid positions), camera, game
                if not building_tiles:
                    return None

                animation = anim_class(
                    building_tiles=building_tiles,
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ in ["InoculantAnimation", "HarvestAnimation"]:
                # ORDNANCE GRAFT skills - full signature; Harvest reads bombed units off game.
                # Inoculant is shared by the graft and the drone (same display name) but they
                # get DIFFERENT animations: the graft sweeps the linstock, the drone shoots a
                # bomb projectile. Pick the variant by the caster's unit type.
                build_cls = anim_class
                if anim_class.__name__ == "InoculantAnimation":
                    from boneglaive.utils.constants import UnitType
                    caster_gu = getattr(caster_unit, 'game_unit', None)
                    if getattr(caster_gu, 'type', None) == UnitType.ORDNANCE_DRONE:
                        build_cls = DroneInoculantAnimation
                animation = build_cls(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ in ["HornswoggleAnimation", "TopiaryBreathAnimation"]:
                # Landscaper directional skills - read data from game unit
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "DissonanceAnimation":
                # Landscaper terrain shatter - needs target position and game
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=target_unit,
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game'),
                    target_x=kwargs.get('target_x', 0),
                    target_y=kwargs.get('target_y', 0)
                )
            elif anim_class.__name__ in ["SlagWallDespawnAnimation", "TopiaryRevertAnimation"]:
                # Landscaper terrain despawn/revert animations
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=None,
                    target_pos=target_pos,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    camera=camera,
                    game=kwargs.get('game'),
                    target_x=kwargs.get('target_x', 0),
                    target_y=kwargs.get('target_y', 0)
                )
            elif anim_class.__name__ == "RespawnAnimation":
                # Respawn - Unit rises from ground with bone particles
                # Requires: caster_unit (respawning unit), target_pos, camera, particle_emitter, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=caster_unit,  # Same as caster for respawn
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=kwargs.get('game')
                )
            elif anim_class.__name__ == "AutoclaveFailureAnimation":
                # Autoclave Failure - GLAIVEMAN charges energy but fizzles (no targets)
                # Requires: caster_unit (GLAIVEMAN), target_pos, camera, particle_emitter, callbacks
                if not target_pos:
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_unit=caster_unit,  # Same as caster for failure animation
                    target_pos=target_pos,
                    is_crit=is_crit,
                    is_infused=is_infused,
                    particle_emitter=particle_emitter,
                    debris_list=[],
                    screen_shake_callback=screen_shake_callback,
                    screen_flash_callback=screen_flash_callback,
                    units_list=units_list if units_list else [],
                    camera=camera,
                    game=game
                )
            else:
                # Most animations expect just target coordinates
                animation = anim_class(**kwargs)

            return animation
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    @classmethod
    def has_animation(cls, skill_name: str) -> bool:
        """Check if a skill has an animation defined."""
        skill_key = skill_name.upper().replace(" ", "_")
        anim_data = cls.SKILL_ANIMATIONS.get(skill_key)
        return anim_data is not None and anim_data[0] is not None
