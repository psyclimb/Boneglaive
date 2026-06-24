#!/usr/bin/env python3
"""
Game State Adapter
Bridges the game logic with the graphical renderer.
"""
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import existing game logic
# Adjust path to find boneglaive.game modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import actual game classes
from boneglaive.game.engine import Game
class AnimationEvent:
    """Represents an animation that needs to be played."""
    def __init__(self, event_type: str, source_unit, target_unit=None, **kwargs):
        self.event_type = event_type  # "skill", "movement", "damage", "death", etc.
        self.source_unit = source_unit
        self.target_unit = target_unit
        self.kwargs = kwargs  # Additional data (skill_name, damage_amount, etc.)


class VisualUnit:
    """Visual representation of a game unit."""
    def __init__(self, game_unit, animated_unit, game):
        self.game_unit = game_unit  # Reference to logic unit
        self.animated_unit = animated_unit  # Reference to visual unit
        self.last_hp = game_unit.hp
        self.last_position = (game_unit.x, game_unit.y)  # Screen coords (x, y), not game coords (y, x)
        # Note: Game units don't have AP, they have action points per turn
        self.last_ap = 0
        self.last_skill = None  # Track last used skill
        self.last_attack_target = None  # Track last basic attack target
        # Track passive skill activation (for Autoclave, etc.)
        self.last_passive_activated = self._get_passive_activation_state(game_unit)
        # Track status effects
        self.last_status_effects = self._get_status_effects(game_unit)
        # Track geas taunt status for geas break heal animation
        self.last_taunted_units = self._get_taunted_units(game_unit, game)
        # Track trapped_by status for trap release animation
        self.last_trapped_by = getattr(game_unit, 'trapped_by', None)
        # Track vagal run duration for abreaction animation
        self.last_vagal_run_duration = getattr(game_unit, 'vagal_run_duration', 0)
        # Track demilune zone duration to detect when upgraded Demilune creates a new zone
        self.last_demilune_zone_duration = 0  # Deprecated — zone mechanic replaced by Selenic Backdraft status
        # Track derelicted duration to detect when upgraded Derelict creates buildings
        self.last_derelicted_duration = getattr(game_unit, 'derelicted_duration', 0)
        # Track autoclave_failure_shown to detect failed Autoclave activation
        self.last_autoclave_failure_shown = getattr(game_unit, 'autoclave_failure_shown', False)

    def _get_passive_activation_state(self, game_unit):
        """Get current activation state of passive skill."""
        if hasattr(game_unit, 'passive_skill') and game_unit.passive_skill:
            if hasattr(game_unit.passive_skill, 'activated'):
                return game_unit.passive_skill.activated
        return False

    def _get_taunted_units(self, game_unit, game):
        """
        Get dict of units taunted by this Potpourrist with their current taunt durations.
        Returns a dict of {unit_id: taunt_duration}.
        This allows detecting both when taunts are cleared AND when duration decreases.
        """
        taunted = {}

        if not game or not game.units:
            return taunted

        # Check all units for taunts
        taunt_count = 0
        for unit in game.units:
            has_taunted_by = hasattr(unit, 'taunted_by')
            taunted_by_this = has_taunted_by and unit.taunted_by == game_unit
            has_duration = hasattr(unit, 'taunt_duration')
            duration_positive = has_duration and unit.taunt_duration > 0

            if taunted_by_this and duration_positive:
                taunted[id(unit)] = unit.taunt_duration
                taunt_count += 1

        return taunted

    def _get_status_effects(self, game_unit):
        """
        Get current status effects on a unit.
        Returns a dict of {effect_name: is_active}
        """
        return get_unit_status_effects(game_unit)


def get_unit_status_effects(game_unit):
    """
    Get current status effects on a unit.
    Returns a dict of {effect_name: is_active}.
    Module-level function so it can be called from both VisualUnit and AnimatedUnit.
    """
    effects = {}

    # Map status effect attributes to icon names
    # Check various status effect flags
    if hasattr(game_unit, 'was_pried') and game_unit.was_pried:
        effects['pry'] = True
    if hasattr(game_unit, 'trapped_by') and game_unit.trapped_by:
        effects['trapped'] = True
    if hasattr(game_unit, 'jawline_affected') and game_unit.jawline_affected:
        effects['jawline'] = True
    if hasattr(game_unit, 'estranged') and game_unit.estranged:
        effects['estranged'] = True
    if hasattr(game_unit, 'mired') and game_unit.mired:
        effects['mired'] = True
    if hasattr(game_unit, 'gaussian_dusk_recharge') and game_unit.gaussian_dusk_recharge > 0:
        effects['recharging'] = True
    if hasattr(game_unit, 'shrapnel_duration') and game_unit.shrapnel_duration > 0:
        effects['shrapnel'] = True
    if hasattr(game_unit, 'radiation_stacks') and len(game_unit.radiation_stacks) > 0:
        effects['radiation_burn'] = True
    if hasattr(game_unit, 'neural_shunt_affected') and game_unit.neural_shunt_affected:
        effects['neural_shunt'] = True
    if hasattr(game_unit, 'carrier_rave_active') and game_unit.carrier_rave_active:
        effects['carrier_rave'] = True
    if hasattr(game_unit, 'trauma_processing_active') and game_unit.trauma_processing_active:
        effects['parallax'] = True  # Trauma Processing uses parallax icon
    if hasattr(game_unit, 'derelicted') and game_unit.derelicted:
        effects['derelicted'] = True
    if hasattr(game_unit, 'status_disarmed') and game_unit.status_disarmed:
        effects['disarmed'] = True
    from boneglaive.utils.constants import UnitType
    if hasattr(game_unit, 'type') and game_unit.type == UnitType.MANDIBLE_FOREMAN:
        if hasattr(game_unit, '_game') and game_unit._game:
            if any(u.is_alive() and u.trapped_by is game_unit for u in game_unit._game.units):
                effects['disarmed'] = True
    if hasattr(game_unit, 'is_topiary') and game_unit.is_topiary:
        effects['topiary'] = True
    # The on-grid status icon picks the numbered variant (bomb1..bomb4) matching the
    # stack count, so the floating icon shows how many bombs are grafted. The count is
    # clamped to BOMB_MAX_STACKS (the icon set tops out there). The side panels are a
    # separate path (glyph + "N turns" duration) and are unaffected by this key.
    _bomb_count = len(getattr(game_unit, 'bombs', []) or [])
    if _bomb_count > 0:
        from boneglaive.utils.constants import BOMB_MAX_STACKS
        effects[f'bomb{min(_bomb_count, BOMB_MAX_STACKS)}'] = True
    if hasattr(game_unit, 'partition_shield_active') and game_unit.partition_shield_active:
        effects['partition'] = True
    if hasattr(game_unit, 'severance_active') and game_unit.severance_active:
        effects['severance'] = True
    if hasattr(game_unit, 'demilune_debuffed') and game_unit.demilune_debuffed:
        effects['lunacy'] = True  # Demilune uses lunacy icon
    if hasattr(game_unit, 'selenic_backdraft') and game_unit.selenic_backdraft:
        effects['selenic_backdraft'] = True
    if hasattr(game_unit, 'geas_affected') and game_unit.geas_affected:
        effects['geas'] = True
    if hasattr(game_unit, 'infusion_stacks') and game_unit.infusion_stacks > 0:
        effects['infusion'] = True
    if hasattr(game_unit, 'potpourri_held') and game_unit.potpourri_held:
        effects['infusion'] = True  # Potpourrist's infuse uses infusion icon
    if hasattr(game_unit, 'ossify_active') and game_unit.ossify_active:
        effects['ossify'] = True
    if hasattr(game_unit, 'site_inspection_marked') and game_unit.site_inspection_marked:
        effects['site_inspection'] = True
    if hasattr(game_unit, 'status_site_inspection') and game_unit.status_site_inspection:
        effects['site_inspection'] = True
    if hasattr(game_unit, 'status_site_inspection_partial') and game_unit.status_site_inspection_partial:
        effects['site_inspection_partial'] = True
    if hasattr(game_unit, 'valuation_oracle_active') and game_unit.valuation_oracle_active:
        effects['valuation_oracle'] = True
    if hasattr(game_unit, 'valuation_oracle_buff') and game_unit.valuation_oracle_buff:
        effects['valuation_oracle'] = True
    if hasattr(game_unit, 'vagal_run_active') and game_unit.vagal_run_active:
        effects['vagal_run'] = True
    if hasattr(game_unit, 'auction_curse_dot') and game_unit.auction_curse_dot:
        effects['auction_curse'] = True
    if hasattr(game_unit, 'investment_active') and game_unit.investment_active:
        effects['investment'] = True
    if hasattr(game_unit, 'can_use_anchor') and game_unit.can_use_anchor:
        effects['parallax'] = True
    if hasattr(game_unit, 'market_futures_bonus_applied') and game_unit.market_futures_bonus_applied:
        effects['investment'] = True
    if hasattr(game_unit, 'first_turn_move_bonus') and game_unit.first_turn_move_bonus:
        effects['first_turn_move_bonus'] = True

    return effects


class GameStateAdapter:
    """
    Adapter between game logic and graphical renderer.

    Responsibilities:
    - Maintain connection to game logic
    - Detect state changes (HP, position, status effects)
    - Generate animation events
    - Translate player input from renderer to game commands
    - Keep visual units synchronized with game units
    """

    def __init__(self):
        # Game logic instance (headless)
        self.game: Optional[Game] = None

        # AI interface (if playing vs AI)
        self.ai_interface = None

        # Visual state
        self.visual_units: Dict[str, VisualUnit] = {}  # unit_id (UUID) -> VisualUnit
        self.animation_queue: List[AnimationEvent] = []
        self.executing_turn = False  # Track if we're in turn execution
        self.post_execution_sync = False  # Track if we're in post-execution sync (for attack animations)

        # State tracking
        self.current_turn = 0
        self.active_unit_id = None
        self.game_phase = "idle"  # "idle", "player_turn", "enemy_turn", "animating", "game_over"

        # Input state
        self.selected_unit_id = None
        self.selected_skill = None
        self.awaiting_target = False

        # Status effect tracking for detecting new effects during turn execution
        # Maps unit_id -> dict of {effect_name: is_active}
        self.status_effects_snapshot: Dict[str, Dict[str, bool]] = {}

        # Scalar node tracking for detecting trap triggers
        # Maps (y, x) position -> {'owner': unit, 'damage': int, 'active': bool}
        self.last_scalar_nodes: Dict[Tuple[int, int], Dict[str, Any]] = {}

        # Revealed scalar node traps (for visual display in graphical mode)
        # Set of (y, x) positions that have been revealed by Site Inspection
        self.revealed_scalar_nodes: set = set()

    def initialize_game(self, game_instance=None, skip_setup=False, map_name="hard_pressed", game_mode="single", ui_adapter=None):
        """
        Initialize or attach to a game instance.

        Args:
            game_instance: Existing game instance, or None to create new
            skip_setup: If False (default), game starts in setup phase where players place units
            map_name: Name of the map to use
            game_mode: Game mode ("single", "vs_ai", "local")
            ui_adapter: GraphicalUIAdapter for AI animations
        """
        if game_instance:
            self.game = game_instance
        else:
            # Create new game instance
            # skip_setup=False means game starts in setup phase
            self.game = Game(skip_setup=skip_setup, map_name=map_name)

        # Initialize AI if in vs_ai mode
        if game_mode == "vs_ai":
            from boneglaive.ai.ai_interface import AIInterface
            self.ai_interface = AIInterface()
            self.ai_interface.initialize(self.game, ui=ui_adapter)

        # Register callbacks for detecting status effects
        self.game.pre_status_clear_callback = self._detect_status_effects_callback
        self.game.post_passive_application_callback = self._detect_passive_status_effects_callback

        # Add UUID system to all units for unique identification
        self._add_unit_ids()

        # Initialize turn tracking
        self.current_turn = self.game.turn

    def _add_unit_ids(self):
        """Add UUID to each unit for unique identification."""
        import uuid
        if not self.game:
            return

        for unit in self.game.units:
            if not hasattr(unit, 'uuid'):
                unit.uuid = str(uuid.uuid4())

    def create_visual_unit(self, game_unit, animated_unit):
        """
        Register a visual unit that corresponds to a game logic unit.

        Args:
            game_unit: The game logic unit
            animated_unit: The AnimatedUnit from the renderer
        """
        unit_id = self._get_unit_id(game_unit)
        self.visual_units[unit_id] = VisualUnit(game_unit, animated_unit, self.game)

    def _get_unit_id(self, unit) -> str:
        """Get unique ID for a unit."""
        if hasattr(unit, 'uuid'):
            return unit.uuid
        else:
            # Fallback: generate UUID if not present
            import uuid
            unit.uuid = str(uuid.uuid4())
            return unit.uuid

    def snapshot_status_effects(self):
        """
        Capture a snapshot of all current status effects on all units.
        This should be called BEFORE execute_turn() so we can detect
        status effects that are applied during turn execution and then cleared.
        """
        if not self.game:
            return

        self.status_effects_snapshot.clear()

        for unit in self.game.units:
            if not unit.is_alive():
                continue

            unit_id = self._get_unit_id(unit)

            # Get status effects using the same logic as VisualUnit
            if unit_id in self.visual_units:
                effects = self.visual_units[unit_id]._get_status_effects(unit)
                self.status_effects_snapshot[unit_id] = effects.copy()

    def snapshot_unit_positions(self):
        """
        Capture a snapshot of all current unit positions.
        This should be called BEFORE execute_turn() so we can detect
        movement skills that succeeded or failed based on position changes.
        """
        if not self.game:
            return

        for unit in self.game.units:
            if not unit.is_alive():
                continue

            unit_id = self._get_unit_id(unit)

            # Store position in visual unit for comparison after turn execution
            if unit_id in self.visual_units:
                self.visual_units[unit_id].last_position = (unit.x, unit.y)

    def _detect_status_effects_callback(self):
        """
        Callback invoked by game engine right before status effects are cleared.
        This is the PERFECT time to detect status effects, as they're still set
        but about to be cleared. Store them for display after damage numbers.
        """
        if not self.game or not self.executing_turn:
            return


        # Clear any previous pending effects
        if not hasattr(self, '_effects_to_show_after_damage'):
            self._effects_to_show_after_damage = []
        else:
            self._effects_to_show_after_damage.clear()

        # Check each unit for status effects
        for unit in self.game.units:
            if not unit.is_alive():
                continue

            unit_id = self._get_unit_id(unit)
            if unit_id not in self.visual_units:
                continue

            visual_unit = self.visual_units[unit_id]

            # Get current status effects (flags are still set!)
            current_status_effects = visual_unit._get_status_effects(unit)

            # Compare against snapshot to find newly applied effects
            if unit_id in self.status_effects_snapshot:
                snapshot_effects = self.status_effects_snapshot[unit_id]

                for effect_name in current_status_effects:
                    if effect_name not in snapshot_effects:
                        # New status effect detected!
                        # Store this for showing after damage numbers
                        self._effects_to_show_after_damage.append((unit_id, effect_name))

        # After detecting turn-based status effects, check for initial Valuation Oracle applications
        # These were applied during game setup before any snapshot was taken
        for unit in self.game.units:
            if (unit.is_alive() and
                hasattr(unit, 'valuation_oracle_initial_application') and
                unit.valuation_oracle_initial_application):
                # Queue this unit for status icon flash
                unit_id = self._get_unit_id(unit)
                if unit_id in self.visual_units:
                    self._effects_to_show_after_damage.append((unit_id, 'valuation_oracle'))
                # Clear the flag so it only triggers once
                unit.valuation_oracle_initial_application = False

    def _detect_passive_status_effects_callback(self):
        """
        Callback invoked by game engine AFTER passive skills are applied at turn start.
        This detects status effects applied by passive skills (like Valuation Oracle).
        """
        if not self.game:
            return

        # Initialize the effects list if needed
        if not hasattr(self, '_effects_to_show_after_damage'):
            self._effects_to_show_after_damage = []

        # Check each unit for Valuation Oracle that was just applied
        for unit in self.game.units:
            if not unit.is_alive():
                continue

            # Check if this unit has the initial application flag
            if (hasattr(unit, 'valuation_oracle_initial_application') and
                unit.valuation_oracle_initial_application):

                unit_id = self._get_unit_id(unit)

                if unit_id in self.visual_units:
                    # Queue the status icon flash
                    self._effects_to_show_after_damage.append((unit_id, 'valuation_oracle'))

                # Clear the flag
                unit.valuation_oracle_initial_application = False

    def sync_state(self) -> List[AnimationEvent]:
        """
        Synchronize visual state with game state.
        Detects changes and generates animation events.

        Returns:
            List of animation events that need to be played
        """
        if not self.game:
            return []

        events = []

        # Detect changes for each unit
        for unit_id, visual_unit in self.visual_units.items():
            game_unit = visual_unit.game_unit
            animated_unit = visual_unit.animated_unit

            # Check for partition dissociation (emergency trigger) FIRST
            # This must be checked BEFORE HP changes because dissociation prevents the HP change!
            # Use partition_dissociation_caster (saved before clearing) instead of partition_shield_caster
            if (hasattr(game_unit, 'partition_shield_blocked_fatal') and
                game_unit.partition_shield_blocked_fatal and
                hasattr(game_unit, 'partition_dissociation_caster') and
                game_unit.partition_dissociation_caster):

                # Only trigger if we haven't already animated this dissociation
                if not hasattr(visual_unit, 'dissociation_animated') or not visual_unit.dissociation_animated:
                    derelictionist = game_unit.partition_dissociation_caster
                    events.append(AnimationEvent(
                        "partition_dissociation",
                        source_unit=derelictionist,  # DERELICTIONIST who cast partition
                        target_unit=game_unit,  # Protected unit that triggered dissociation
                    ))
                    # Mark as animated to prevent re-triggering
                    visual_unit.dissociation_animated = True
            elif hasattr(visual_unit, 'dissociation_animated') and visual_unit.dissociation_animated:
                # Reset flag when the game logic clears the blocked_fatal flag
                if not (hasattr(game_unit, 'partition_shield_blocked_fatal') and game_unit.partition_shield_blocked_fatal):
                    visual_unit.dissociation_animated = False

            # Detect vagal run abreaction (delayed effect trigger)
            current_vagal_duration = getattr(game_unit, 'vagal_run_duration', 0)
            if visual_unit.last_vagal_run_duration > 0 and current_vagal_duration == 0:
                # Abreaction just triggered! (duration went from >0 to 0)
                caster = getattr(game_unit, 'vagal_run_caster', None)
                events.append(AnimationEvent(
                    "skill",
                    source_unit=caster,  # DERELICTIONIST who cast Vagal Run (may be None if dead)
                    target_unit=game_unit,  # Unit experiencing abreaction
                    skill_name="VAGAL_RUN_ABREACTION",  # Use abreaction version (no connection arc)
                    skill_target=(game_unit.y, game_unit.x)  # Must be skill_target, not target_pos!
                ))

            # Update last vagal run duration
            visual_unit.last_vagal_run_duration = current_vagal_duration

            # Detect HP changes
            current_hp = game_unit.hp

            if current_hp != visual_unit.last_hp:
                hp_delta = current_hp - visual_unit.last_hp

                # Skip damage/death animations for expired summons (vapors, doppelgangers timing out)
                is_expired_summon = getattr(game_unit, '_expired_summon', False)

                if hp_delta < 0 and not is_expired_summon:
                    # Check if unit just entered critical health (retching)
                    # Must check BEFORE updating last_hp
                    if (visual_unit.last_hp > game_unit.get_critical_threshold() and
                        game_unit.is_at_critical_health()):
                        # Unit just crossed into critical health - trigger retch animation!
                        events.append(AnimationEvent(
                            "retch",
                            source_unit=None,
                            target_unit=game_unit
                        ))

                    # Damage taken - check if from scalar node trap
                    unit_pos = (game_unit.y, game_unit.x)
                    scalar_trap_triggered = False

                    # Check if this position had a scalar node that's now gone
                    current_scalar_nodes = getattr(self.game, 'scalar_nodes', {})
                    if unit_pos in self.last_scalar_nodes and unit_pos not in current_scalar_nodes:
                        # Scalar node was here and is now gone - it triggered!
                        node_info = self.last_scalar_nodes[unit_pos]
                        owner = node_info['owner']

                        events.append(AnimationEvent(
                            "scalar_trap",
                            source_unit=owner,  # INTERFERER who placed the trap
                            target_unit=game_unit,  # Victim
                            trap_position=unit_pos,
                            damage_amount=abs(hp_delta)
                        ))
                        scalar_trap_triggered = True

                    # Check if this is trap tick damage (unit is currently trapped)
                    trap_tick_damage = False
                    if hasattr(game_unit, 'trapped_by') and game_unit.trapped_by and not scalar_trap_triggered:
                        # Unit is trapped - this damage is from trap tick
                        events.append(AnimationEvent(
                            "viseroy_tick",
                            source_unit=game_unit.trapped_by,  # MANDIBLE_FOREMAN who owns trap
                            target_unit=game_unit,  # Trapped victim
                            damage_amount=abs(hp_delta)
                        ))
                        trap_tick_damage = True

                    # Check if this is Auction Curse DOT damage
                    auction_curse_tick = False
                    if hasattr(game_unit, 'auction_curse_dot') and game_unit.auction_curse_dot and not scalar_trap_triggered and not trap_tick_damage:
                        # Unit is cursed - this damage is from Auction Curse DOT
                        # Find the DELPHIC_APPRAISER who cast the curse
                        caster_player = 3 - game_unit.player  # Opposing player
                        appraiser_unit = None
                        for u in self.game.units:
                            if u.is_alive() and u.player == caster_player:
                                from boneglaive.utils.constants import UnitType
                                if u.type == UnitType.DELPHIC_APPRAISER:
                                    appraiser_unit = u
                                    break

                        events.append(AnimationEvent(
                            "skill",
                            source_unit=appraiser_unit,  # DELPHIC_APPRAISER who cast curse (may be None if dead)
                            target_unit=game_unit,  # Cursed victim
                            skill_name="AUCTION_CURSE_TICK",
                            skill_target=(game_unit.y, game_unit.x)  # Position of cursed unit
                        ))
                        auction_curse_tick = True

                    if not scalar_trap_triggered and not trap_tick_damage and not auction_curse_tick:
                        # Regular damage (not from scalar trap or Viseroy tick)
                        events.append(AnimationEvent(
                            "damage",
                            source_unit=None,
                            target_unit=game_unit,
                            damage_amount=abs(hp_delta)
                        ))
                elif hp_delta > 0:
                    # Healing - check if it's from geas break or Melange Eminence

                    # Check if this is Melange Eminence passive healing (POTPOURRIST only)
                    is_melange_heal = False
                    geas_break_units = []

                    from boneglaive.utils.constants import UnitType
                    if game_unit.type == UnitType.POTPOURRIST:
                        # Check if POTPOURRIST has geas_heal_sources list (set when geas breaks)
                        if hasattr(game_unit, 'geas_heal_sources') and game_unit.geas_heal_sources:
                            geas_break_units = game_unit.geas_heal_sources
                            # Clear the marker
                            game_unit.geas_heal_sources = []
                        elif hp_delta in (1, 2):
                            # Melange Eminence heals 1 HP normally, 2 HP when holding potpourri
                            is_melange_heal = True
                            is_infused = getattr(game_unit, 'potpourri_held', False)

                    if is_melange_heal:
                        # Melange Eminence passive heal
                        events.append(AnimationEvent(
                            "melange_heal",
                            source_unit=game_unit,  # POTPOURRIST healing self
                            target_unit=game_unit,
                            heal_amount=hp_delta,
                            infused=is_infused
                        ))
                    elif geas_break_units:
                        # Geas break heals - create animation for EACH breaking unit
                        # Each unit contributes 4 HP of healing (or whatever remains if hitting max HP)
                        # Total heal is hp_delta, divide evenly for display purposes
                        remaining_heal = hp_delta
                        num_units = len(geas_break_units)

                        for i, geas_break_unit in enumerate(geas_break_units):
                            # For even distribution of heal display
                            if i == num_units - 1:
                                # Last unit gets any remainder
                                unit_heal = remaining_heal
                            else:
                                unit_heal = hp_delta // num_units
                                remaining_heal -= unit_heal

                            events.append(AnimationEvent(
                                "geas_heal",
                                source_unit=geas_break_unit,  # Unit that had geas
                                target_unit=game_unit,  # Potpourrist healing
                                heal_amount=unit_heal  # Show portion of heal from this unit
                            ))
                    else:
                        # Regular heal
                        events.append(AnimationEvent(
                            "heal",
                            source_unit=None,
                            target_unit=game_unit,
                            heal_amount=hp_delta
                        ))

                visual_unit.last_hp = current_hp

                # Check for death (skip for expired summons — they just fade out)
                if current_hp <= 0 and not is_expired_summon:
                    events.append(AnimationEvent(
                        "death",
                        source_unit=game_unit,
                        target_unit=game_unit
                    ))

                    # Check for Rail Genesis death explosion (FOWL CONTRIVANCE passive)
                    if (hasattr(game_unit, 'type') and
                        str(game_unit.type) == "UnitType.FOWL_CONTRIVANCE"):
                        # FOWL CONTRIVANCE died - trigger Rail Genesis explosion animation
                        # Note: Rails may already be removed by game logic, but animation captures positions at init
                        events.append(AnimationEvent(
                            "skill",
                            source_unit=game_unit,
                            target_unit=None,
                            skill_name="RAIL_GENESIS_DEATH_EXPLOSION",
                            skill_target=None
                        ))

                    # Check for Bone Tithe death healing (MARROW CONDENSER upgraded passive)
                    if (hasattr(game_unit, 'type') and
                        str(game_unit.type) == "UnitType.MARROW_CONDENSER"):
                        # Check if Bone Tithe is upgraded and has accumulated HP
                        from boneglaive.game.upgrades import UpgradeManager
                        if UpgradeManager.is_skill_upgraded(game_unit, "Bone Tithe"):
                            bone_tithe_hp = getattr(game_unit, 'bone_tithe_hp_gained', 0)
                            if bone_tithe_hp > 0:
                                # Find allies in 5x5 area around death position
                                affected_allies = []
                                death_pos = (game_unit.y, game_unit.x)

                                for dy in range(-2, 3):
                                    for dx in range(-2, 3):
                                        if dy == 0 and dx == 0:
                                            continue  # Skip center
                                        tile_y, tile_x = death_pos[0] + dy, death_pos[1] + dx

                                        # Find unit at this position
                                        for unit_id, other_unit in self.visual_units.items():
                                            other_game = other_unit.game_unit
                                            if (other_game and other_game.is_alive() and
                                                other_game.y == tile_y and other_game.x == tile_x and
                                                other_game.player == game_unit.player):
                                                # Skip summons (doppelgangers and vapors)
                                                from boneglaive.utils.constants import UnitType
                                                if other_game.type == UnitType.HEINOUS_VAPOR:
                                                    break
                                                if hasattr(other_game, 'is_doppelganger') and other_game.is_doppelganger:
                                                    break
                                                # Check if this ally can be healed (not cursed)
                                                if not (hasattr(other_game, 'auction_curse_no_heal') and other_game.auction_curse_no_heal):
                                                    affected_allies.append(other_game)
                                                break

                                if affected_allies:
                                    # Calculate heal per ally (distributed evenly)
                                    heal_per_ally = bone_tithe_hp // len(affected_allies)

                                    # Build affected_allies list with individual heal amounts
                                    affected_allies_data = []
                                    for ally in affected_allies:
                                        affected_allies_data.append({
                                            'unit': ally,
                                            'heal': heal_per_ally
                                        })

                                    # Queue death heal animation
                                    events.append(AnimationEvent(
                                        "skill",
                                        source_unit=game_unit,
                                        target_unit=None,
                                        skill_name="BONE_TITHE_DEATH_HEAL",
                                        skill_target=death_pos,
                                        death_pos=death_pos,
                                        affected_allies=affected_allies_data,
                                        heal_amount=heal_per_ally
                                    ))

                    # Check for Auction Curse Soul Collection (DELPHIC APPRAISER upgrade)
                    if (hasattr(game_unit, 'auction_curse_caster') and game_unit.auction_curse_caster):
                        caster = game_unit.auction_curse_caster
                        from boneglaive.game.upgrades import UpgradeManager
                        if UpgradeManager.is_skill_upgraded(caster, "Auction Curse"):
                            # Check for perfect timing (initial_hp == applied_duration)
                            initial_hp = getattr(game_unit, 'auction_curse_initial_hp', 0)
                            applied_duration = getattr(game_unit, 'auction_curse_applied_duration', 0)
                            if initial_hp > 0 and initial_hp == applied_duration:
                                # Soul collection animation triggers
                                death_pos = (game_unit.y, game_unit.x)
                                events.append(AnimationEvent(
                                    "skill",
                                    source_unit=caster,
                                    target_unit=game_unit,
                                    skill_name="AUCTION_CURSE_SOUL_COLLECTION",
                                    skill_target=death_pos
                                ))

            # Detect Granite Geas chain hit (marked by skill when chaining)
            if hasattr(game_unit, 'granite_geas_chain_hit') and game_unit.granite_geas_chain_hit:
                # This unit was hit by Granite Geas (either primary or chained)
                # Create animation event for it
                infused = getattr(game_unit, 'granite_geas_infused', False)

                # Find the caster (POTPOURRIST who cast Granite Geas)
                caster = game_unit.taunted_by if hasattr(game_unit, 'taunted_by') else None

                if caster:
                    events.append(AnimationEvent(
                        "skill",
                        source_unit=caster,
                        target_unit=game_unit,
                        skill_name="GRANITE_GEAS",
                        skill_target=(game_unit.y, game_unit.x),
                        is_infused=infused
                    ))

                # Clear the marker so we don't re-trigger the animation
                game_unit.granite_geas_chain_hit = False
                if hasattr(game_unit, 'granite_geas_infused'):
                    delattr(game_unit, 'granite_geas_infused')

            # Clear geas breaking marker if set (used for detecting which unit's geas broke)
            if hasattr(game_unit, 'geas_breaking_for_animation') and game_unit.geas_breaking_for_animation:
                game_unit.geas_breaking_for_animation = False

            # Detect partition shield hit — spawn reverberation animation
            if hasattr(game_unit, 'partition_hit_for_animation') and game_unit.partition_hit_for_animation:
                game_unit.partition_hit_for_animation = False
                events.append(AnimationEvent(
                    "partition_hit",
                    source_unit=game_unit,
                    target_unit=game_unit
                ))

            # Detect position changes
            # VisualUnit tracks screen coords (x, y), not game coords (y, x)
            current_pos = (game_unit.x, game_unit.y)
            if current_pos != visual_unit.last_position:
                # Check if this is an off-map position (e.g., GAS_MACHINIST Diverge uses -999, -999)
                # Treat off-map positions as instant teleports to avoid long walking animations
                is_off_map = game_unit.x < 0 or game_unit.y < 0 or game_unit.x >= 100 or game_unit.y >= 100

                # Check if this position change is due to a pending teleport skill
                is_teleport = hasattr(visual_unit, 'pending_teleport_skill') and visual_unit.pending_teleport_skill
                if is_teleport:
                    # Clear the pending teleport flag
                    visual_unit.pending_teleport_skill = None

                # Check if this unit was abducted by Delta Config (upgraded)
                is_abducted = hasattr(game_unit, 'abducted_by_delta_config') and game_unit.abducted_by_delta_config
                if is_abducted:
                    # Clear the abduction flag
                    game_unit.abducted_by_delta_config = False
                    # Treat as teleport to prevent walk cycle
                    is_teleport = True

                # ORDNANCE_DRONE relocated by Skyhook (carried with the graft): snap it
                # instantly, no walk cycle. The Skyhook animation hides it until landing.
                if getattr(game_unit, 'skyhook_relocated', False):
                    game_unit.skyhook_relocated = False
                    is_teleport = True

                # Check if this is a DERELICTIONIST defection teleport (partition dissociation)
                is_defection_teleport = (hasattr(game_unit, 'pending_teleport_defection') and
                                        game_unit.pending_teleport_defection)
                if is_defection_teleport:
                    origin = getattr(game_unit, 'teleport_origin', visual_unit.last_position)
                    destination = getattr(game_unit, 'teleport_destination', current_pos)
                    # Generate teleport defection event
                    events.append(AnimationEvent(
                        "teleport_defection",
                        source_unit=game_unit,
                        origin_pos=origin,  # (y, x) in game coords
                        destination_pos=destination  # (y, x) in game coords
                    ))

                    # Clear teleport flags
                    game_unit.pending_teleport_defection = False
                    if hasattr(game_unit, 'teleport_origin'):
                        delattr(game_unit, 'teleport_origin')
                    if hasattr(game_unit, 'teleport_destination'):
                        delattr(game_unit, 'teleport_destination')

                    # Update visual position directly (no walking)
                    visual_unit.last_position = current_pos

                    # Update grid coordinates
                    animated_unit.grid_x = game_unit.x
                    animated_unit.grid_y = game_unit.y

                    # Calculate and update screen coordinates (must include GRID_OFFSET)
                    from boneglaive.graphical.animations.core import TILE_SIZE
                    from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y

                    new_x = game_unit.x * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
                    new_y = game_unit.y * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y

                    # Set both current position and target position (so no walking animation)
                    animated_unit.x = new_x
                    animated_unit.y = new_y
                    animated_unit.target_x = new_x
                    animated_unit.target_y = new_y
                    animated_unit.is_moving = False  # Important: disable walking animation

                elif is_off_map:
                    # Off-map position (e.g., GAS_MACHINIST Diverge) - instant position update, no walking
                    visual_unit.last_position = current_pos

                    # Update grid coordinates
                    animated_unit.grid_x = game_unit.x
                    animated_unit.grid_y = game_unit.y

                    # For off-map positions, just update position without calculating screen coords
                    # The unit will be hidden by the renderer anyway
                    animated_unit.is_moving = False

                elif not is_teleport:
                    # Normal movement - generate movement event and animate walking
                    events.append(AnimationEvent(
                        "movement",
                        source_unit=game_unit,
                        old_position=visual_unit.last_position,
                        new_position=current_pos
                    ))
                    visual_unit.last_position = current_pos

                    # Sync visual position
                    # Game uses (y, x), visual uses (grid_x, grid_y)
                    # grid_x = x (column), grid_y = y (row)
                    # Note: move_to_grid doesn't account for GRID_OFFSET, so we need to adjust
                    animated_unit.move_to_grid(game_unit.x, game_unit.y)

                    # move_to_grid doesn't account for GRID_OFFSET, so adjust manually
                    from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
                    animated_unit.target_x += GRID_OFFSET_X
                    animated_unit.target_y += GRID_OFFSET_Y
                else:
                    # Teleport skill - update last_position and sync grid position but don't animate walking
                    # The skill animation will handle the visual teleportation effect
                    visual_unit.last_position = current_pos

                    # Sync the visual unit's grid position to match game logic
                    # Game uses (y, x), visual uses (grid_x, grid_y)
                    # grid_x = x (column), grid_y = y (row)
                    animated_unit.grid_x = game_unit.x
                    animated_unit.grid_y = game_unit.y

            # Detect basic attack ONLY during POST-execution sync
            # Attacks get set when planned, but we only want to animate them AFTER validation in execute_turn
            # This prevents false attack animations when AI plans attacks that fail validation (range/LOS)
            if self.executing_turn and self.post_execution_sync:
                # Check for executed attacks (stored before action targets are cleared)
                if hasattr(game_unit, 'last_executed_attack') and game_unit.last_executed_attack:
                    # Check if this is a new attack (not already animated)
                    if game_unit.last_executed_attack != visual_unit.last_attack_target:
                        # Basic attack is being executed!
                        attack_target = game_unit.last_executed_attack  # (y, x) in game coords

                        # Use the status effects snapshot (taken BEFORE execute_turn) to check
                        # carrier_rave state, since the engine clears carrier_rave_active during execution
                        has_carrier_rave = False
                        unit_id = self._get_unit_id(game_unit)
                        if unit_id in self.status_effects_snapshot:
                            has_carrier_rave = self.status_effects_snapshot[unit_id].get('carrier_rave', False)

                        # Capture target unit for passive skill detection (e.g. Riposte)
                        target_game_unit = self.game.get_unit_at(attack_target[0], attack_target[1]) if attack_target else None

                        # Capture target's riposte_active state BEFORE attack execution clears it
                        target_has_riposte = False
                        if target_game_unit:
                            if (hasattr(target_game_unit, 'passive_skill') and target_game_unit.passive_skill and
                                target_game_unit.passive_skill.name == "Riposte" and
                                hasattr(target_game_unit, 'riposte_active') and target_game_unit.riposte_active):
                                target_has_riposte = True

                        events.append(AnimationEvent(
                            "attack",
                            source_unit=game_unit,
                            target_unit=target_game_unit,
                            attack_target=attack_target,
                            has_carrier_rave=has_carrier_rave,  # Pass flag to renderer
                            target_has_riposte=target_has_riposte  # Pass flag to renderer
                        ))
                        visual_unit.last_attack_target = game_unit.last_executed_attack
                        # Clear the executed attack flag after detecting it
                        game_unit.last_executed_attack = None
                elif visual_unit.last_attack_target is not None:
                    # Attack was cleared - reset our tracking
                    visual_unit.last_attack_target = None

            # Detect skill usage ONLY during turn execution
            # Skills get set when planned, but we only want to animate them when executed
            if self.executing_turn:
                if hasattr(game_unit, 'selected_skill') and game_unit.selected_skill:
                    # Check if this skill hasn't been animated yet
                    if game_unit.selected_skill != visual_unit.last_skill:
                        # Skill is being executed!
                        skill_target = getattr(game_unit, 'skill_target', None)
                        skill_name = game_unit.selected_skill.name if hasattr(game_unit.selected_skill, 'name') else str(game_unit.selected_skill)

                        # Gaussian Dusk no longer needs special handling (fires immediately, no charging)

                        # Track if this is a teleport/movement skill that will change position
                        # These skills have their own animation and should not show walking animation
                        teleport_skills = ["Delta Config", "Vault", "Expedite", "Parallax", "Skyhook"]
                        if skill_name in teleport_skills:
                            # Store this in visual_unit so we can check it when detecting position changes
                            visual_unit.pending_teleport_skill = skill_name

                        # Capture Potpourrist's infusion state BEFORE skill execution clears it
                        is_infused = False
                        if skill_name in ["Demilune", "Granite Geas"] and hasattr(game_unit, 'potpourri_held'):
                            is_infused = game_unit.potpourri_held

                        # Capture MANDIBLE FOREMAN's expedite_planned_start BEFORE skill execution clears it
                        # This is needed for move+Expedite combos where the foreman starts from a planned move position
                        expedite_planned_start = None
                        if skill_name == "Expedite" and hasattr(game_unit, 'expedite_planned_start'):
                            expedite_planned_start = game_unit.expedite_planned_start

                        # Capture target unit BEFORE skill execution (units may move during execution)
                        target_game_unit = None
                        if skill_target:
                            target_game_unit = self.game.get_unit_at(skill_target[0], skill_target[1])

                        # Bounce count for ricochet-style animations
                        bounce_count = 2  # default

                        # Check if skill is upgraded and modify skill_name for upgraded animations
                        # This allows the animation factory to use upgraded animation variants
                        if skill_name == "Vault":
                            from boneglaive.game.upgrades import UpgradeManager
                            if UpgradeManager.is_skill_upgraded(game_unit, "Vault"):
                                skill_name = "Vault_Upgraded"  # Use upgraded animation variant
                        elif skill_name == "Site Inspection":
                            from boneglaive.game.upgrades import UpgradeManager
                            if UpgradeManager.is_skill_upgraded(game_unit, "Site Inspection"):
                                skill_name = "Site Inspection_Upgraded"  # Use upgraded animation variant
                        elif skill_name == "Jawline":
                            from boneglaive.game.upgrades import UpgradeManager
                            if UpgradeManager.is_skill_upgraded(game_unit, "Jawline"):
                                skill_name = "Jawline_Upgraded"  # Use upgraded animation variant
                        elif skill_name == "Demilune":
                            from boneglaive.game.upgrades import UpgradeManager
                            if UpgradeManager.is_skill_upgraded(game_unit, "Demilune"):
                                skill_name = "Demilune_Upgraded"  # Use upgraded animation variant

                        # MOVE+SKILL POSITION FIX: Use move_target position if unit is moving
                        # When move+skill are queued, game_unit.x/y is still at OLD position during pre-sync
                        # but move_target contains the NEW position where skill will execute from
                        position_dependent_skills = ["Gaussian Dusk", "Parabol", "Big Arc", "Fragcrest", "Pry"]
                        if skill_name in position_dependent_skills and hasattr(game_unit, 'move_target') and game_unit.move_target:
                            # Unit is moving this turn - use move_target as the firing position
                            target_y, target_x = game_unit.move_target

                            # Update AnimatedUnit to fire from the move_target position
                            animated_unit.grid_x = target_x
                            animated_unit.grid_y = target_y

                            # Also update screen position to prevent visual glitches
                            from boneglaive.graphical.animations.core import TILE_SIZE
                            from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y

                            new_x = target_x * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
                            new_y = target_y * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y

                            # Snap to new position (movement animation will play before skill animation)
                            animated_unit.x = new_x
                            animated_unit.y = new_y
                            animated_unit.target_x = new_x
                            animated_unit.target_y = new_y
                            animated_unit.is_moving = False

                        events.append(AnimationEvent(
                            "skill",
                            source_unit=game_unit,
                            target_unit=target_game_unit,  # Pass actual unit, not None
                            skill_name=skill_name,
                            skill_target=skill_target,
                            is_infused=is_infused,
                            bounce_count=bounce_count,
                            expedite_planned_start=expedite_planned_start
                        ))

                        # Special handling for Site Inspection: mark revealed scalar nodes
                        if skill_name == "Site Inspection" and skill_target and hasattr(self.game, 'scalar_nodes'):
                            # Site Inspection reveals enemy scalar nodes in 3x3 area around target
                            y, x = skill_target
                            for dy in [-1, 0, 1]:
                                for dx in [-1, 0, 1]:
                                    check_y = y + dy
                                    check_x = x + dx
                                    check_pos = (check_y, check_x)

                                    # Check if there's a scalar node at this position
                                    if check_pos in self.game.scalar_nodes:
                                        node_info = self.game.scalar_nodes[check_pos]
                                        owner = node_info['owner']

                                        # Only reveal enemy scalar nodes
                                        if owner.player != game_unit.player:
                                            # Mark this node as revealed for visual display
                                            self.revealed_scalar_nodes.add(check_pos)

                        visual_unit.last_skill = game_unit.selected_skill
                elif visual_unit.last_skill is not None:
                    # Skill was cleared - reset our tracking
                    visual_unit.last_skill = None

            # Detect Glaive Sweep execution (upgraded Autoclave counter-attack)
            if hasattr(game_unit, 'last_executed_glaive_sweep') and game_unit.last_executed_glaive_sweep:
                events.append(AnimationEvent(
                    "glaive_sweep",
                    source_unit=game_unit,
                    target_unit=None
                ))
                game_unit.last_executed_glaive_sweep = None

            # Status effect detection now happens via callback
            # Update last_status_effects for tracking
            current_status_effects = visual_unit._get_status_effects(game_unit)
            visual_unit.last_status_effects = current_status_effects

            # Detect passive skill activation (e.g., Autoclave)
            # Check if passive skill state changed from inactive to active
            current_passive_activated = visual_unit._get_passive_activation_state(game_unit)
            if current_passive_activated and not visual_unit.last_passive_activated:
                # Passive skill just activated!
                if hasattr(game_unit, 'passive_skill') and game_unit.passive_skill:
                    passive_name = game_unit.passive_skill.name
                    # Queue animation for passive skill activation
                    events.append(AnimationEvent(
                        "skill",
                        source_unit=game_unit,
                        target_unit=None,
                        skill_name=passive_name.upper(),
                        skill_target=None
                    ))

                    visual_unit.last_passive_activated = True

            # Detect Autoclave failure (no targets)
            current_autoclave_failure = getattr(game_unit, 'autoclave_failure_shown', False)
            if current_autoclave_failure and not visual_unit.last_autoclave_failure_shown:
                # Autoclave just failed to activate due to no targets!
                events.append(AnimationEvent(
                    "autoclave_failure",
                    source_unit=game_unit,
                    target_unit=game_unit
                ))
                visual_unit.last_autoclave_failure_shown = True

            # Update autoclave failure tracking
            if not current_autoclave_failure and visual_unit.last_autoclave_failure_shown:
                # Reset flag when unit clears it
                visual_unit.last_autoclave_failure_shown = False

            # Detect trap releases (Viseroy trap)
            current_trapped_by = getattr(game_unit, 'trapped_by', None)
            if visual_unit.last_trapped_by and not current_trapped_by:
                # Unit was trapped and is now released!
                trapper_unit = visual_unit.last_trapped_by
                events.append(AnimationEvent(
                    "trap_release",
                    source_unit=trapper_unit,  # MANDIBLE FOREMAN who set the trap
                    target_unit=game_unit  # Unit being released
                ))

            # Update trapped_by tracking
            visual_unit.last_trapped_by = current_trapped_by

            # Clean up any leftover geas_heal_sources list (safety measure)
            if hasattr(game_unit, 'geas_heal_sources'):
                game_unit.geas_heal_sources = []

            # Update taunted units snapshot at end of each sync cycle
            # This ensures we have the "before" state for next cycle's geas heal detection
            new_taunted = visual_unit._get_taunted_units(game_unit, self.game)
            visual_unit.last_taunted_units = new_taunted


            # Detect Derelict building creation (upgraded Derelict only)
            # Buildings are created during skill execution when Derelicted status is applied
            current_derelicted_duration = getattr(game_unit, 'derelicted_duration', 0)
            if current_derelicted_duration > 0 and visual_unit.last_derelicted_duration == 0:
                # Unit just got derelicted! Check if buildings were created around it
                if hasattr(self.game, 'derelict_building_tiles') and self.game.derelict_building_tiles:
                    # Find buildings that are centered on this unit (or close to it)
                    # Buildings are in a 3x3 circle around the derelicted unit
                    unit_pos = (game_unit.y, game_unit.x)
                    nearby_building_tiles = []

                    for tile_pos in self.game.derelict_building_tiles.keys():
                        # Check if this tile is within range of the unit (roughly 3x3 area)
                        dy = abs(tile_pos[0] - unit_pos[0])
                        dx = abs(tile_pos[1] - unit_pos[1])
                        if dy <= 2 and dx <= 2:
                            nearby_building_tiles.append(tile_pos)

                    if nearby_building_tiles:
                        pass

                        # Create building formation event
                        events.append(AnimationEvent(
                            "building_create",
                            source_unit=game_unit,
                            building_tiles=nearby_building_tiles
                        ))

            # Update derelicted duration tracking
            visual_unit.last_derelicted_duration = current_derelicted_duration

        # Check for Derelict push trails
        if hasattr(self.game, 'derelict_push_trails') and self.game.derelict_push_trails:
            for push_trail in self.game.derelict_push_trails:
                events.append(AnimationEvent(
                    "push_trail",
                    source_unit=None,  # Visual effect only, no specific source
                    start_pos=push_trail['start_pos'],
                    end_pos=push_trail['end_pos']
                ))
            # Clear processed trails
            self.game.derelict_push_trails = []

        # Status effects are shown after damage numbers via _show_active_status_effects()
        # in the renderer, using _effects_to_show_after_damage populated by the callback

        # Update scalar node tracking for next sync
        if hasattr(self.game, 'scalar_nodes'):
            self.last_scalar_nodes = self.game.scalar_nodes.copy()

            # Clean up revealed nodes that have been triggered/destroyed
            # Remove positions from revealed set if node no longer exists
            revealed_to_remove = []
            for revealed_pos in self.revealed_scalar_nodes:
                if revealed_pos not in self.game.scalar_nodes:
                    revealed_to_remove.append(revealed_pos)

            for pos in revealed_to_remove:
                self.revealed_scalar_nodes.discard(pos)

        # Check for HEINOUS VAPOR units that just applied AOE effects
        # (marked by execute_turn before applying effects)
        # NOTE: Skip vapors that just spawned this turn (they have their own spawn animation)
        if self.game:
            from boneglaive.utils.constants import UnitType
            for unit in self.game.units:
                if (unit.is_alive() and
                    unit.type == UnitType.HEINOUS_VAPOR and
                    hasattr(unit, 'just_applied_aoe') and
                    unit.just_applied_aoe and
                    hasattr(unit, 'vapor_type')):

                    # Queue vapor AOE tick animation
                    vapor_type = unit.vapor_type
                    skill_name = f"vapor_aoe_{vapor_type.lower()}"

                    events.append(AnimationEvent(
                        "skill",
                        source_unit=unit,
                        target_unit=None,
                        skill_name=skill_name,
                        skill_target=(unit.y, unit.x)  # Vapor's position
                    ))

                    # Clear the flag
                    unit.just_applied_aoe = False

        # Clear Gaussian Dusk sync flags after processing
        for unit_id, visual_unit in self.visual_units.items():
            if hasattr(visual_unit, 'gaussian_dusk_fired_this_sync'):
                visual_unit.gaussian_dusk_fired_this_sync = False

        # Include any queued animation events (vapor AOE ticks, etc.)
        if self.animation_queue:
            events.extend(self.animation_queue)
            self.animation_queue.clear()

        # Check for dead GRAYMAN ECHO units (before returning events)
        # Detect doppelganger deaths and trigger explosion animation
        dead_doppelganger_ids = []
        for unit_id, visual_unit in list(self.visual_units.items()):
            game_unit = visual_unit.game_unit

            # Check if this is a dead doppelganger
            if (hasattr(game_unit, 'is_doppelganger') and
                game_unit.is_doppelganger and
                not game_unit.is_alive()):

                # Check if we haven't already triggered death animation for this doppelganger
                if not hasattr(visual_unit, 'doppelganger_death_animated') or not visual_unit.doppelganger_death_animated:
                    # Queue death explosion animation
                    events.append(AnimationEvent(
                        "skill",
                        source_unit=game_unit,
                        target_unit=None,
                        skill_name="GRAYMAN_ECHO_DEATH",
                        skill_target=(game_unit.y, game_unit.x)
                    ))

                    # Mark as animated to prevent re-triggering
                    visual_unit.doppelganger_death_animated = True
                    dead_doppelganger_ids.append(unit_id)

        # Check for triggered Fragcrest traps
        if hasattr(self.game, 'triggered_fragcrest_traps') and self.game.triggered_fragcrest_traps:
            for trap_info in self.game.triggered_fragcrest_traps:
                trap_pos = trap_info['trap_pos']
                owner = trap_info['owner']
                triggering_unit = trap_info['triggering_unit']
                affected_positions = trap_info['affected_positions']
                units_with_shrapnel = trap_info.get('units_with_shrapnel', [])


                # Create skill animation event for Fragcrest at trap position
                # Note: skill_name must be "FRAGCREST" (all caps) to match AnimationFactory registration
                # Note: target_unit is required by FragcrestAnimation, use triggering unit
                # Note: is_trap=True tells animation to originate from trap_pos instead of caster position
                # Note: trap_cone_positions provides pre-calculated cone positions for the trap
                events.append(AnimationEvent(
                    "skill",
                    source_unit=owner,
                    target_unit=triggering_unit,
                    skill_name="FRAGCREST",
                    skill_target=trap_pos,  # (y, x) position of trap
                    is_trap=True,  # Flag to make animation originate from trap position
                    trap_cone_positions=affected_positions  # Pre-calculated cone positions
                ))

                # NOTE: Shrapnel status effect icons are now handled via detection system
                # (_detect_status_effects_callback) to prevent duplicate flashes.
                # The shrapnel effect will be detected and shown ONCE after damage completes.

            # Clear triggered traps list
            self.game.triggered_fragcrest_traps = []

        # Detect slag wall despawns (LANDSCAPER Hornswoggle)
        if hasattr(self.game, 'last_despawned_slag_walls') and self.game.last_despawned_slag_walls:
            for pos_y, pos_x in self.game.last_despawned_slag_walls:
                events.append(AnimationEvent(
                    "skill",
                    source_unit=None,
                    target_unit=None,
                    skill_name="SLAG_WALL_DESPAWN",
                    skill_target=(pos_y, pos_x)))
            self.game.last_despawned_slag_walls = []

        # Detect topiary reverts (LANDSCAPER Topiary Breath)
        if hasattr(self.game, 'last_reverted_topiaries') and self.game.last_reverted_topiaries:
            for pos_y, pos_x in self.game.last_reverted_topiaries:
                events.append(AnimationEvent(
                    "skill",
                    source_unit=None,
                    target_unit=None,
                    skill_name="TOPIARY_REVERT",
                    skill_target=(pos_y, pos_x)))
            self.game.last_reverted_topiaries = []

        return events

    def queue_skill_animation(self, skill_name: str, caster, target=None, **kwargs):
        """
        Queue a skill animation to be played.

        Args:
            skill_name: Name of the skill (e.g., "glaive_judgement")
            caster: Unit casting the skill
            target: Target unit (if applicable)
            **kwargs: Additional skill-specific data
        """
        event = AnimationEvent(
            "skill",
            source_unit=caster,
            target_unit=target,
            skill_name=skill_name,
            **kwargs
        )
        self.animation_queue.append(event)

    def queue_vapor_aoe_tick(self, vapor_unit):
        """
        Queue a vapor AOE tick animation when vapor applies area effects.
        Called as callback from vapor AOE processing.

        Args:
            vapor_unit: The HEINOUS_VAPOR unit applying AOE effects
        """
        if not vapor_unit or not hasattr(vapor_unit, 'vapor_type'):
            return

        # Create skill name for animation factory
        vapor_type = vapor_unit.vapor_type
        skill_name = f"vapor_aoe_{vapor_type.lower()}"

        # Queue animation at vapor's position
        event = AnimationEvent(
            "skill",
            source_unit=vapor_unit,
            target_unit=None,
            skill_name=skill_name,
            target_pos=(vapor_unit.y, vapor_unit.x)  # Game coords (y, x)
        )
        self.animation_queue.append(event)

    def get_movement_range(self, game_unit) -> List[Tuple[int, int]]:
        """
        Get valid movement positions for a unit.

        Args:
            game_unit: The game logic unit

        Returns:
            List of (x, y) tuples in renderer coordinates (column, row)
        """
        if not self.game or not game_unit:
            return []

        # Get possible moves from game (returns list of (y, x) tuples)
        possible_moves = self.game.get_possible_moves(game_unit)

        # Convert from game coordinates (y, x) to renderer coordinates (x, y)
        # Game: (y, x) = (row, col)
        # Renderer: (x, y) = (col, row)
        movement_range = [(x, y) for (y, x) in possible_moves]

        return movement_range

    def get_attack_range(self, game_unit, from_pos=None) -> List[Tuple[int, int]]:
        """
        Get valid attack positions for a unit.

        Args:
            game_unit: The game logic unit
            from_pos: Optional (y, x) position to calculate attack range from (for ghost position)

        Returns:
            List of (x, y) tuples in renderer coordinates (column, row)
        """
        if not self.game or not game_unit:
            return []

        # Get possible attacks from game (returns list of (y, x) tuples)
        # Pass from_pos to calculate from ghost position if unit has pending move
        possible_attacks = self.game.get_possible_attacks(game_unit, from_pos=from_pos)

        # Convert from game coordinates (y, x) to renderer coordinates (x, y)
        # Game: (y, x) = (row, col)
        # Renderer: (x, y) = (col, row)
        attack_range = [(x, y) for (y, x) in possible_attacks]

        return attack_range

    def get_skill_range(self, game_unit, skill) -> List[Tuple[int, int]]:
        """
        Get valid target positions for a skill.

        Args:
            game_unit: The game logic unit
            skill: The skill object

        Returns:
            List of (x, y) tuples in renderer coordinates (column, row)
        """
        if not self.game or not game_unit or not skill:
            return []

        skill_range_positions = []

        # Get unit's position (or planned move position)
        from_y = game_unit.y
        from_x = game_unit.x
        if game_unit.move_target:
            from_y, from_x = game_unit.move_target

        # Special case for Gaussian Dusk - only show cardinal direction lines
        if skill.name == "Gaussian Dusk":
            # Show four cardinal direction lines from unit position
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # East, West, South, North
            for dy, dx in directions:
                y, x = from_y, from_x
                # Trace line in this direction across the map
                while True:
                    y += dy
                    x += dx
                    # Stop if we go off the map
                    if not (0 <= y < self.game.map.height and 0 <= x < self.game.map.width):
                        break
                    # Convert to renderer coords and add
                    skill_range_positions.append((x, y))

        # Hornswoggle / Topiary Breath: show all 8 adjacent tiles as direction selectors
        elif skill.name in ("Hornswoggle", "Topiary Breath"):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    adj_y = from_y + dy
                    adj_x = from_x + dx
                    if self.game.is_valid_position(adj_y, adj_x):
                        skill_range_positions.append((adj_x, adj_y))
        else:
            # Special handling for Vault - check for upgrade before calculating range
            if skill.name == "Vault":
                from boneglaive.game.upgrades import UpgradeManager
                is_upgraded = UpgradeManager.is_skill_upgraded(game_unit, "Vault")
                skill.range = 3 if is_upgraded else 2

            # Get skill range (check for dynamic range method first)
            if hasattr(skill, 'get_skill_range') and callable(skill.get_skill_range):
                skill_range = skill.get_skill_range(game_unit, self.game)
            elif hasattr(skill, 'get_range') and callable(skill.get_range):
                skill_range = skill.get_range(game_unit)
            else:
                skill_range = skill.range

            # Check all positions within range
            for y in range(max(0, from_y - skill_range), min(self.game.map.height, from_y + skill_range + 1)):
                for x in range(max(0, from_x - skill_range), min(self.game.map.width, from_x + skill_range + 1)):
                    # Calculate distance
                    distance = self.game.chess_distance(from_y, from_x, y, x)
                    if distance > skill_range:
                        continue

                    # Check if skill can be used on this position
                    can_use_result = skill.can_use(game_unit, (y, x), self.game)

                    # Debug logging for Diverge skill
                    if skill.name == "Diverge":
                        target_unit = self.game.get_unit_at(y, x)
                        if target_unit:
                            pass
                        else:
                            pass

                    if can_use_result:
                        # Convert to renderer coords
                        skill_range_positions.append((x, y))

        return skill_range_positions

    def handle_player_action(self, action_type: str, **kwargs) -> bool:
        """
        Handle player input and translate to game logic.

        Args:
            action_type: Type of action ("select_unit", "move", "use_skill", "end_turn")
            **kwargs: Action-specific parameters

        Returns:
            True if action was valid and executed
        """
        if not self.game:
            return False

        if action_type == "select_unit":
            unit_id = kwargs.get("unit_id")
            self.selected_unit_id = unit_id
            self.selected_skill = None
            self.awaiting_target = False
            return True

        elif action_type == "select_skill":
            skill_name = kwargs.get("skill_name")
            self.selected_skill = skill_name
            self.awaiting_target = True
            return True

        elif action_type == "target_skill":
            if not self.selected_unit_id or not self.selected_skill:
                return False

            target_id = kwargs.get("target_id")

            # Reset state
            self.selected_skill = None
            self.awaiting_target = False
            return True

        elif action_type == "move_unit":
            if not self.selected_unit_id:
                return False

            target_x = kwargs.get("grid_x")
            target_y = kwargs.get("grid_y")

            return True

        elif action_type == "end_turn":
            return True

        return False

