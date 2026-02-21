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
    MelangeEminenceHealAnimation, MelangeEminenceInfusedHealAnimation,
    SelenicBackdraftZone
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
    MarketFuturesAnimation,
    MarketFuturesTeleportAnimation,
    DeftRerollAnimation,
)
from boneglaive.graphical.animations.marrow_condenser import (
    OssifyAnimation,
    BoneTitheAnimation,
    MarrowDikeAnimation,
    MarrowDikeWallDespawnAnimation,
)
from boneglaive.graphical.animations.derelictionist import (
    PartitionAnimation,
    PartitionHitAnimation,
    VagalRunAnimation,
    VagalRunAbreactionAnimation,
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
from boneglaive.graphical.animations.pelotari import (
    MatadorAnimation,
    RiposteAnimation,
    PoachAnimation,
    BackhandAnimation,
    BackhandReflectionAnimation,
)
from boneglaive.graphical.animations.core_animations import (
    RespawnAnimation,
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
        "SELENIC_BACKDRAFT": (SelenicBackdraftZone, {}),  # Persistent zone for upgraded Demilune
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
        "DERELICT_BUILDING_FORMATION": (DerelictBuildingFormation, {}),  # Building rising animation
        "DERELICT_BUILDING_TILES": (DerelictBuildingTiles, {}),  # Persistent building tiles

        # PELOTARI skills (DLC)
        "MATADOR": (MatadorAnimation, {}),
        "POACH": (PoachAnimation, {}),
        "BACKHAND": (BackhandAnimation, {}),
        "BACKHAND_REFLECTION": (BackhandReflectionAnimation, {}),

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

        # DEBUG: Log all Gaussian Dusk related calls
        if "GAUSSIAN" in skill_key or "DUSK" in skill_key:
            print(f"[AnimationFactory] ========== GAUSSIAN DUSK ANIMATION FACTORY ==========")
            print(f"[AnimationFactory]   Original skill_name: '{skill_name}'")
            print(f"[AnimationFactory]   Normalized skill_key: '{skill_key}'")
            print(f"[AnimationFactory]   Caster unit: {caster_unit}")
            if hasattr(caster_unit, 'game_unit'):
                print(f"[AnimationFactory]   Caster game_unit: {caster_unit.game_unit}")
                if hasattr(caster_unit.game_unit, 'charging_status'):
                    print(f"[AnimationFactory]   charging_status: {caster_unit.game_unit.charging_status}")

        # Check for special variants
        if skill_key == "DEMILUNE":
            # Check if caster has infusion buff (TODO: implement check)
            # For now, use regular demilune
            pass

        # Gaussian Dusk animations are now differentiated by skill name at event creation
        # "Gaussian Dusk Charge" -> GAUSSIAN_DUSK_CHARGE
        # "Gaussian Dusk Fire" -> GAUSSIAN_DUSK_FIRE
        # No state checking needed here anymore

        # Check for Fragcrest trap mode (override class before lookup)
        if skill_key == "FRAGCREST" and kwargs.get('is_trap', False):
            print("[AnimationFactory] FRAGCREST trap mode detected - using FragcrestTrapAnimation")
            anim_data = (FragcrestTrapAnimation, {})
        else:
            # Get animation class and kwargs from registry
            anim_data = cls.SKILL_ANIMATIONS.get(skill_key)

        # DEBUG: Log lookup result
        if "GAUSSIAN" in skill_key or "DUSK" in skill_key:
            print(f"[AnimationFactory]   Looking up '{skill_key}' in SKILL_ANIMATIONS...")
            print(f"[AnimationFactory]   Found: {anim_data is not None}")
            if anim_data:
                print(f"[AnimationFactory]   Animation class: {anim_data[0]}")

        if not anim_data:
            print(f"[AnimationFactory] No animation defined for skill: {skill_name} (key: {skill_key})")
            return None

        anim_class, base_kwargs = anim_data

        if anim_class is None:
            print(f"[AnimationFactory] Animation not implemented yet: {skill_name} (key: {skill_key})")
            return None

        # Play skill sound effect
        sound_key = get_sound_for_skill(skill_name)
        if sound_key:
            try:
                sound_manager = get_sound_manager()
                sound_manager.play(sound_key, category="skills")
            except Exception as e:
                # Don't crash if sound fails - just log it
                print(f"[AnimationFactory] Failed to play sound for {skill_name}: {e}")

        # Prepare animation kwargs
        kwargs = base_kwargs.copy()
        kwargs['game'] = game  # Add game instance to kwargs
        kwargs['bounce_count'] = bounce_count  # Add bounce count for Matador animation

        # Use camera for coordinate conversion (if provided)
        # Falls back to default offsets for backwards compatibility
        if camera:
            grid_to_screen = camera.grid_to_screen
        else:
            # Fallback for older code that doesn't pass camera
            print("[AnimationFactory] WARNING: No camera provided, using default offsets")
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
                print("[AnimationFactory] Warning: No caster or target position provided")
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
                    print(f"[AnimationFactory] Using game_unit position for {skill_name}: ({caster_grid_y}, {caster_grid_x})")
                    print(f"[AnimationFactory] AnimatedUnit position: ({caster_unit.grid_y}, {caster_unit.grid_x})")
                else:
                    # Fall back to AnimatedUnit's position
                    caster_grid_x = caster_unit.grid_x
                    caster_grid_y = caster_unit.grid_y
                    print(f"[AnimationFactory] No game_unit, using AnimatedUnit position: ({caster_grid_y}, {caster_grid_x})")

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
                    print("[AnimationFactory] JUDGEMENT requires a target position")
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
                    direction=0  # TODO: determine direction based on caster facing
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
                    print("[AnimationFactory] PRY requires a target position")
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
                    print("[AnimationFactory] VAULT requires a target position")
                    return None

                # Check if vault was displaced (collision with ally move)
                actual_target_pos = target_pos
                if caster_unit and hasattr(caster_unit, 'game_unit') and hasattr(caster_unit.game_unit, 'vault_displaced_to'):
                    actual_target_pos = caster_unit.game_unit.vault_displaced_to
                    print(f"[AnimationFactory] VAULT displaced from {target_pos} to {actual_target_pos}")
                    # Clear the flag
                    del caster_unit.game_unit.vault_displaced_to

                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=actual_target_pos,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    camera=camera
                )
            elif anim_class.__name__ == "VaultAnimationControllerUpgraded":
                # VaultAnimationControllerUpgraded needs target position (same signature as regular Vault)
                if not target_pos:
                    print("[AnimationFactory] VAULT_UPGRADED requires a target position")
                    return None

                # Check if vault was displaced (collision with ally move)
                actual_target_pos = target_pos
                if caster_unit and hasattr(caster_unit, 'game_unit') and hasattr(caster_unit.game_unit, 'vault_displaced_to'):
                    actual_target_pos = caster_unit.game_unit.vault_displaced_to
                    print(f"[AnimationFactory] VAULT_UPGRADED displaced from {target_pos} to {actual_target_pos}")
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
                    print("[AnimationFactory] DELTA_CONFIG requires a target position")
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
                    print("[AnimationFactory] GRAE_EXCHANGE requires a target position")
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    particle_emitter=particle_emitter,
                    camera=camera
                )
            elif anim_class.__name__ == "GraymanEchoDeathExplosionAnimation":
                # GRAYMAN ECHO death explosion - psychic explosion affecting 3x3 area
                # Requires: caster_unit (dead echo), camera, standard callbacks
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
                # DemiluneSwing needs caster, target positions, and infused flag
                # Use the is_infused parameter passed from the event (captured before skill execution)
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    caster_unit=caster_unit,
                    target_x=kwargs.get('target_x', caster_screen_x),
                    target_y=kwargs.get('target_y', caster_screen_y),
                    infused=is_infused,  # Use the parameter, not the game state
                    targets=units_list,  # Pass all units so animation can detect hits
                    # Pass grid positions for accurate arc calculation
                    caster_grid_pos=(caster_unit.grid_y, caster_unit.grid_x) if hasattr(caster_unit, 'grid_y') else None,
                    target_grid_pos=target_pos,
                    camera=camera
                )
            elif anim_class.__name__ == "GraniteGeasEffect":
                # GraniteGeasEffect needs target position and target unit
                if not target_unit:
                    print("[AnimationFactory] GRANITE_GEAS requires a target unit")
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
                    print("[AnimationFactory] MELANGE_EMINENCE_HEAL requires a target position")
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
                # Neutron Illuminant animations need caster position, particle emitter, and screen flash callback
                print(f"[AnimationFactory] Creating {anim_class.__name__} at ({caster_screen_x}, {caster_screen_y})")
                animation = anim_class(
                    caster_x=caster_screen_x,
                    caster_y=caster_screen_y,
                    caster_unit=caster_unit,
                    particle_emitter=particle_emitter,
                    screen_flash_callback=screen_flash_callback
                )
                print(f"[AnimationFactory] Created animation: {animation}")
            elif anim_class.__name__ == "NeuralShuntAnimation":
                # Neural Shunt needs caster, target positions, and callbacks
                if not target_unit:
                    print("[AnimationFactory] NEURAL_SHUNT requires a target unit")
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
                # Karrier Rave triple strike (melee attack with Neutron Illuminant patterns)
                if not target_unit:
                    print("[AnimationFactory] KARRIER_RAVE_STRIKE requires a target unit")
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
                        print("[AnimationFactory] JAWLINE_UPGRADED requires a target position")
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
                    print("[AnimationFactory] EXPEDITE requires a target position")
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
                    print(f"[AnimationFactory] Expedite using planned start position: grid ({planned_y}, {planned_x}) -> screen ({caster_screen_x}, {caster_screen_y})")

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
                    print("[AnimationFactory] DIVINE_DEPRECIATION requires a target position (furniture)")
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
                    print("[AnimationFactory] AUCTION_CURSE requires a target position (enemy unit)")
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
                    print("[AnimationFactory] MARKET_FUTURES requires a target position (furniture)")
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
                    print("[AnimationFactory] PARALLAX requires a target position (destination)")
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
                # Bone Tithe - AOE life drain from enemies
                # Upgraded: Range increases from 1 (3x3) to 2 (5x5)
                # Requires: caster unit, units_list (to detect enemies), standard callbacks

                # Check if Bone Tithe is upgraded
                is_upgraded = False
                if caster_unit and hasattr(caster_unit, 'game_unit'):
                    game_unit = caster_unit.game_unit
                    if hasattr(game_unit, 'upgraded_skills') and 'Bone Tithe' in game_unit.upgraded_skills:
                        is_upgraded = True
                elif caster_unit and hasattr(caster_unit, 'upgraded_skills'):
                    if 'Bone Tithe' in caster_unit.upgraded_skills:
                        is_upgraded = True

                # Use upgraded animation if skill is upgraded
                from boneglaive.graphical.animations import BoneTitheAnimationUpgraded
                anim_class_to_use = BoneTitheAnimationUpgraded if is_upgraded else anim_class

                animation = anim_class_to_use(
                    caster_unit=caster_unit,
                    target_unit=None,  # AOE around caster
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
                    print("[AnimationFactory] MARROW_DIKE_WALL_DESPAWN requires a target position")
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
                    print("[AnimationFactory] PARTITION requires a target unit")
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
                    print("[AnimationFactory] VAGAL_RUN requires a target unit")
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
                    print("[AnimationFactory] VAGAL_RUN_ABREACTION requires a target unit")
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
            elif anim_class.__name__ == "ParabolAnimation":
                # Parabol - 3x3 mortar barrage with indirect fire
                # Check if skill is upgraded (uses underground parabola with second explosion)
                # Requires: target_pos (center of 3x3 area), camera, callbacks
                if not target_pos:
                    print("[AnimationFactory] PARABOL requires a target position")
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
                    print("[AnimationFactory] FRAGCREST requires a target position")
                    return None
                if not target_unit:
                    print("[AnimationFactory] FRAGCREST requires a target unit")
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
                print(f"[AnimationFactory] Creating GaussianDuskFireAnimation")
                print(f"[AnimationFactory]   caster_unit: {caster_unit}")
                print(f"[AnimationFactory]   target_pos (direction): {target_pos}")
                print(f"[AnimationFactory]   camera: {camera}")
                if not target_pos:
                    print("[AnimationFactory] ERROR: GAUSSIAN_DUSK_FIRE requires a target position (direction)")
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
                print(f"[AnimationFactory] GaussianDuskFireAnimation created successfully")
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
                    print("[AnimationFactory] DIVERGE requires a target position")
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
                    print("[AnimationFactory] AEROSOLIZE_ARMS requires a target position")
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
                    print("[AnimationFactory] AUCTION_CURSE_TICK requires a target position")
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
            elif anim_class.__name__ == "MatadorAnimation":
                # Matador - MASSIVE pelota projectile with multi-bounce ricochet
                # Requires: caster_unit, target_pos, camera, particle_emitter, game, bounce_count
                if not target_pos:
                    print("[AnimationFactory] MATADOR requires a target position")
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
                    print("[AnimationFactory] POACH requires a target position")
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
            elif anim_class.__name__ == "SelenicBackdraftZone":
                # Selenic Backdraft Zone - Persistent ground effect for upgraded Demilune
                # Requires: zone_tiles (list of grid positions), caster_unit, camera, game
                if not zone_tiles:
                    print("[AnimationFactory] ERROR: SelenicBackdraftZone requires zone_tiles")
                    return None

                animation = anim_class(
                    zone_tiles=zone_tiles,
                    caster_unit=caster_unit,
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ == "DerelictBuildingFormation":
                # Derelict Building Formation - Building rising animation
                # Requires: building_tiles (list of grid positions), camera, game
                if not building_tiles:
                    print("[AnimationFactory] ERROR: DerelictBuildingFormation requires building_tiles")
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
                    print("[AnimationFactory] ERROR: DerelictBuildingTiles requires building_tiles")
                    return None

                animation = anim_class(
                    building_tiles=building_tiles,
                    camera=camera,
                    game=game
                )
            elif anim_class.__name__ == "RespawnAnimation":
                # Respawn - Unit rises from ground with bone particles
                # Requires: caster_unit (respawning unit), target_pos, camera, particle_emitter, callbacks
                if not target_pos:
                    print("[AnimationFactory] RESPAWN requires a target position")
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
                    print("[AnimationFactory] AUTOCLAVE_FAILURE requires a target position")
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

            print(f"[AnimationFactory] Created {anim_class.__name__} for {skill_name}")
            return animation
        except Exception as e:
            print(f"[AnimationFactory] Error creating animation for {skill_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @classmethod
    def has_animation(cls, skill_name: str) -> bool:
        """Check if a skill has an animation defined."""
        skill_key = skill_name.upper().replace(" ", "_")
        anim_data = cls.SKILL_ANIMATIONS.get(skill_key)
        return anim_data is not None and anim_data[0] is not None
