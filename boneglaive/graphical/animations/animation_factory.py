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
    LightningBolt, CrossBeam, AutoclaveAnimation, SpinningGlaiveProjectile,
    PryImpactAnimation, VaultAnimationController
)
from boneglaive.graphical.animations.mandible_foreman import (
    JawClamp, ViseroyTrap, ViseroyRelease, SiteInspectionBuff,
    SiteInspectionScan, ExpediteRush, JawlineNetwork
)
from boneglaive.graphical.animations.potpourrist import (
    PedestalStrike, InfuseEffect, DemiluneSwing, GraniteGeasEffect
)
from boneglaive.graphical.animations.grayman import (
    DeltaConfigAnimation,
    GraeExchangeAnimation,
    EstrangeBeam,
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
    MarketFuturesAnimation,
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
)

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
        "JUDGEMENT": (SpinningGlaiveProjectile, {}),
        "PRY": (PryImpactAnimation, {}),  # Simplified impact + debris effect (no displacement)
        "VAULT": (VaultAnimationController, {}),  # Acrobatic leap with flip
        "AUTOCLAVE": (AutoclaveAnimation, {}),  # Cross-shaped steam beams in 4 directions

        # MANDIBLE FOREMAN skills
        "EXPEDITE": (ExpediteRush, {}),  # Discharge skill is named "Expedite"
        "DISCHARGE": (ViseroyRelease, {}),  # Release animation for Viseroy trap (when it ends)
        "SITE_INSPECTION": (SiteInspectionScan, {}),  # Laser scan animation
        "JAWLINE": (JawlineNetwork, {}),  # Network of bear traps
        "VISEROY": (ViseroyTrap, {}),  # Passive (basic attack animation)

        # POTPOURRIST skills
        "PEDESTAL_STRIKE": (PedestalStrike, {}),
        "INFUSE": (InfuseEffect, {}),
        "DEMILUNE": (DemiluneSwing, {}),
        "DEMILUNE_INFUSED": (DemiluneSwing, {"infused": True}),
        "GRANITE_GEAS": (GraniteGeasEffect, {}),

        # GRAYMAN skills
        "DELTA_CONFIG": (DeltaConfigAnimation, {}),
        "ESTRANGE": (EstrangeBeam, {}),
        "GRAE_EXCHANGE": (GraeExchangeAnimation, {}),
        "GRÆ_EXCHANGE": (GraeExchangeAnimation, {}),  # Handle special character

        # MARROW CONDENSER skills
        "OSSIFY": (OssifyAnimation, {}),
        "MARROW_DIKE": (MarrowDikeAnimation, {}),
        "BONE_TITHE": (BoneTitheAnimation, {}),
        "MARROW_DIKE_WALL_DESPAWN": (MarrowDikeWallDespawnAnimation, {}),

        # FOWL CONTRIVANCE skills (TODO: Implement)
        "GAUSSIAN_DUSK": (None, {}),
        "BIG_ARC": (None, {}),
        "FRAGCREST": (None, {}),

        # GAS MACHINIST skills (TODO: Implement)
        "ENBROACHMENT_GAS": (None, {}),
        "SAFT_E_GAS": (None, {}),
        "DIVERGE": (None, {}),

        # DELPHIC APPRAISER skills
        "MARKET_FUTURES": (MarketFuturesAnimation, {}),
        "AUCTION_CURSE": (AuctionCurseAnimation, {}),
        "DIVINE_DEPRECIATION": (DivineDrepreciationAnimation, {}),

        # INTERFERER skills
        "NEUTRON_ILLUMINANT_CARDINAL": (NeutronIlluminantCardinal, {}),
        "NEUTRON_ILLUMINANT_DIAGONAL": (NeutronIlluminantDiagonal, {}),
        "NEURAL_SHUNT": (NeuralShuntAnimation, {}),
        "KARRIER_RAVE": (KarrierRavePhaseOut, {}),
        "KARRIER_RAVE_STRIKE": (KarrierRaveTripleStrike, {}),  # Triple melee attack
        "SCALAR_NODE": (None, {}),  # Trap placement (no animation - silent)

        # DERELICTIONIST skills
        "VAGAL_RUN": (None, {}),  # TODO: Implement
        "DERELICT": (None, {}),  # TODO: Implement
        "PARTITION": (PartitionAnimation, {}),
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
                        game = None):
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
        # Normalize skill name (remove spaces, uppercase)
        skill_key = skill_name.upper().replace(" ", "_")

        # Check for special variants
        if skill_key == "DEMILUNE":
            # Check if caster has infusion buff (TODO: implement check)
            # For now, use regular demilune
            pass

        # Get animation class and kwargs
        anim_data = cls.SKILL_ANIMATIONS.get(skill_key)
        if not anim_data:
            print(f"[AnimationFactory] No animation defined for skill: {skill_name}")
            return None

        anim_class, base_kwargs = anim_data

        if anim_class is None:
            print(f"[AnimationFactory] Animation not implemented yet: {skill_name}")
            return None

        # Prepare animation kwargs
        kwargs = base_kwargs.copy()
        kwargs['game'] = game  # Add game instance to kwargs

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
            target_x, target_y = grid_to_screen(target_pos[0], target_pos[1])
            kwargs['target_x'] = target_x
            kwargs['target_y'] = target_y
        else:
            # Some skills target self or area
            target_x, target_y = grid_to_screen(caster_unit.grid_x, caster_unit.grid_y)
            kwargs['target_x'] = target_x
            kwargs['target_y'] = target_y

        # Create animation instance
        # Different animations have different constructor signatures
        try:
            # Convert caster grid coords to screen coords
            caster_screen_x, caster_screen_y = grid_to_screen(caster_unit.grid_x, caster_unit.grid_y)

            # Most animations expect target_x, target_y (or center_x, center_y)
            # SpinningGlaiveProjectile expects start_x, start_y, target_x, target_y, is_crit
            if anim_class.__name__ == "SpinningGlaiveProjectile":
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
                # AutoclaveAnimation creates all 4 beams at caster position
                animation = anim_class(
                    center_x=caster_screen_x,
                    center_y=caster_screen_y,
                    max_range=3  # Autoclave has range 3
                )
            elif anim_class.__name__ == "PryImpactAnimation":
                # PryImpactAnimation needs special args (particle-based, no debris_list)
                if not target_unit:
                    print("[AnimationFactory] PRY requires a target unit")
                    return None
                animation = anim_class(
                    target_unit=target_unit,
                    caster_unit=caster_unit,
                    particle_emitter=particle_emitter,
                    screen_shake_callback=screen_shake_callback,
                    units_list=units_list
                )
            elif anim_class.__name__ == "VaultAnimationController":
                # VaultAnimationController needs target position
                if not target_pos:
                    print("[AnimationFactory] VAULT requires a target position")
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
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
                if not target_pos:
                    print("[AnimationFactory] DELTA_CONFIG requires a target position")
                    return None
                animation = anim_class(
                    caster_unit=caster_unit,
                    target_pos=target_pos,
                    particle_emitter=particle_emitter,
                    camera=camera
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
                    screen_flash_callback=screen_flash_callback
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
            elif anim_class.__name__ == "SiteInspectionScan":
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
            elif anim_class.__name__ == "JawlineNetwork":
                # Jawline network - deploys from caster position
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
                # Convert grid to screen: target_pos[1] is grid_x, target_pos[0] is grid_y
                target_x, target_y = grid_to_screen(target_pos[1], target_pos[0])
                animation = anim_class(
                    start_x=caster_screen_x,
                    start_y=caster_screen_y,
                    target_x=target_x,
                    target_y=target_y,
                    foreman_unit=caster_unit,
                    target_grid_pos=target_pos,  # Pass grid position for final update
                    camera=camera
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
                # Bone Tithe - AOE life drain from adjacent enemies
                # Requires: caster unit, units_list (to detect adjacent enemies), standard callbacks
                animation = anim_class(
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
