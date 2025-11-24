#!/usr/bin/env python3
"""
Game State Adapter
Bridges the ASCII game logic with the graphical renderer.
"""
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import existing game logic
# Adjust path to find boneglaive.game modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import actual game classes
from boneglaive.game.engine import Game
from boneglaive.game.units import Unit


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
        self.last_position = (game_unit.x, game_unit.y)
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
                print(f"[DEBUG] _get_taunted_units: {unit.get_display_name()} is taunted by {game_unit.get_display_name()} (duration: {unit.taunt_duration})")

        if taunt_count == 0 and hasattr(game_unit, 'unit_class') and game_unit.unit_class and game_unit.unit_class.name == "POTPOURRIST":
            print(f"[DEBUG] _get_taunted_units: {game_unit.get_display_name()} has no taunted units")

        return taunted

    def _get_status_effects(self, game_unit):
        """
        Get current status effects on a unit.
        Returns a dict of {effect_name: is_active}
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
        if hasattr(game_unit, 'charging_status') and game_unit.charging_status:
            effects['charging'] = True
        if hasattr(game_unit, 'shrapnel_duration') and game_unit.shrapnel_duration > 0:
            effects['shrapnel'] = True
        if hasattr(game_unit, 'radiation_stacks') and len(game_unit.radiation_stacks) > 0:
            effects['radiation_sickness'] = True
        if hasattr(game_unit, 'neural_shunt_affected') and game_unit.neural_shunt_affected:
            effects['neural_shunt'] = True
        if hasattr(game_unit, 'carrier_rave_active') and game_unit.carrier_rave_active:
            effects['carrier_rave'] = True
        if hasattr(game_unit, 'trauma_processing_active') and game_unit.trauma_processing_active:
            effects['parallax'] = True  # Trauma Processing uses parallax icon
        if hasattr(game_unit, 'derelicted') and game_unit.derelicted:
            effects['derelicted'] = True
        if hasattr(game_unit, 'partition_shield_active') and game_unit.partition_shield_active:
            effects['partition'] = True
        if hasattr(game_unit, 'severance_active') and game_unit.severance_active:
            effects['severance'] = True
        if hasattr(game_unit, 'demilune_debuffed') and game_unit.demilune_debuffed:
            effects['lunacy'] = True  # Demilune uses lunacy icon
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
        if hasattr(game_unit, 'vagal_run_active') and game_unit.vagal_run_active:
            effects['vagal_run'] = True
        if hasattr(game_unit, 'auction_curse_dot') and game_unit.auction_curse_dot:
            effects['auction_curse'] = True
        if hasattr(game_unit, 'investment_active') and game_unit.investment_active:
            effects['investment'] = True

        return effects


class GameStateAdapter:
    """
    Adapter between ASCII game logic and graphical renderer.

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

        # Visual state
        self.visual_units: Dict[str, VisualUnit] = {}  # unit_id (UUID) -> VisualUnit
        self.animation_queue: List[AnimationEvent] = []
        self.executing_turn = False  # Track if we're in turn execution

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

    def initialize_game(self, game_instance=None, skip_setup=True, map_name="stained_stones"):
        """
        Initialize or attach to a game instance.

        Args:
            game_instance: Existing game instance, or None to create new
            skip_setup: If True, creates game with default units (for testing)
            map_name: Name of the map to use
        """
        if game_instance:
            self.game = game_instance
        else:
            # Create new game instance
            self.game = Game(skip_setup=skip_setup, map_name=map_name)

        # Register callback for detecting status effects before they're cleared
        self.game.pre_status_clear_callback = self._detect_status_effects_callback

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

        print(f"[GameState] Captured status effects snapshot for {len(self.status_effects_snapshot)} units")

    def _detect_status_effects_callback(self):
        """
        Callback invoked by game engine right before status effects are cleared.
        This is the PERFECT time to detect status effects, as they're still set
        but about to be cleared. Store them for display after damage numbers.
        """
        if not self.game or not self.executing_turn:
            return

        print(f"[GameState] *** STATUS DETECTION CALLBACK INVOKED ***")

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

                print(f"[GameState] Callback check {unit.get_display_name()}: was_pried={getattr(unit, 'was_pried', 'N/A')}, current={current_status_effects}, snapshot={snapshot_effects}")

                for effect_name in current_status_effects:
                    if effect_name not in snapshot_effects:
                        # New status effect detected!
                        print(f"[GameState] *** CALLBACK DETECTED NEW STATUS EFFECT '{effect_name}' on {unit.get_display_name()} ***")

                        # Store this for showing after damage numbers
                        self._effects_to_show_after_damage.append((unit_id, effect_name))

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
                    print(f"[GameState] *** PARTITION DISSOCIATION DETECTED! *** {game_unit.get_display_name()} triggered emergency dissociation")
                    print(f"  DERELICTIONIST: {derelictionist.get_display_name()}")
                    print(f"  partition_shield_blocked_fatal: {game_unit.partition_shield_blocked_fatal}")
                    print(f"  partition_dissociation_caster: {game_unit.partition_dissociation_caster}")

                    events.append(AnimationEvent(
                        "partition_dissociation",
                        source_unit=derelictionist,  # DERELICTIONIST who cast partition
                        target_unit=game_unit,  # Protected unit that triggered dissociation
                    ))
                    print(f"  Event created and appended to events list (total events: {len(events)})")

                    # Mark as animated to prevent re-triggering
                    visual_unit.dissociation_animated = True
                    print(f"  Set dissociation_animated flag on visual_unit")
            elif hasattr(visual_unit, 'dissociation_animated') and visual_unit.dissociation_animated:
                # Reset flag when the game logic clears the blocked_fatal flag
                if not (hasattr(game_unit, 'partition_shield_blocked_fatal') and game_unit.partition_shield_blocked_fatal):
                    visual_unit.dissociation_animated = False
                    print(f"[GameState DEBUG] Reset dissociation_animated flag for {game_unit.get_display_name()}")

            # Detect HP changes
            current_hp = game_unit.hp

            if current_hp != visual_unit.last_hp:
                hp_delta = current_hp - visual_unit.last_hp

                if hp_delta < 0:
                    # Damage taken - check if from scalar node trap
                    unit_pos = (game_unit.y, game_unit.x)
                    scalar_trap_triggered = False

                    # Check if this position had a scalar node that's now gone
                    current_scalar_nodes = getattr(self.game, 'scalar_nodes', {})
                    if unit_pos in self.last_scalar_nodes and unit_pos not in current_scalar_nodes:
                        # Scalar node was here and is now gone - it triggered!
                        node_info = self.last_scalar_nodes[unit_pos]
                        owner = node_info['owner']

                        print(f"[GameState] SCALAR NODE TRAP DETECTED! {game_unit.get_display_name()} triggered trap at {unit_pos}")

                        events.append(AnimationEvent(
                            "scalar_trap",
                            source_unit=owner,  # INTERFERER who placed the trap
                            target_unit=game_unit,  # Victim
                            trap_position=unit_pos,
                            damage_amount=abs(hp_delta)
                        ))
                        scalar_trap_triggered = True

                    if not scalar_trap_triggered:
                        # Regular damage (not from scalar trap)
                        events.append(AnimationEvent(
                            "damage",
                            source_unit=None,  # TODO: Track damage source
                            target_unit=game_unit,
                            damage_amount=abs(hp_delta)
                        ))
                elif hp_delta > 0:
                    # Healing - check if it's from geas break
                    current_taunted = visual_unit._get_taunted_units(game_unit, self.game)
                    last_taunted = visual_unit.last_taunted_units

                    print(f"[GameState] {game_unit.get_display_name()} healed {hp_delta} HP")
                    print(f"  Last taunted units: {last_taunted}")
                    print(f"  Current taunted units: {current_taunted}")

                    # Check for geas break: either taunt was removed OR duration decreased
                    geas_break_unit = None
                    if self.game:
                        for unit in self.game.units:
                            unit_id = id(unit)
                            # Was this unit taunted before?
                            if unit_id in last_taunted:
                                last_duration = last_taunted[unit_id]
                                current_duration = current_taunted.get(unit_id, 0)

                                # If duration decreased or taunt was cleared, that's a geas break
                                if current_duration < last_duration:
                                    geas_break_unit = unit
                                    print(f"  *** GEAS BREAK DETECTED! {unit.get_display_name()} ignored geas (duration {last_duration}->{current_duration}), {game_unit.get_display_name()} heals! ***")
                                    break

                    if geas_break_unit:
                        # Geas break heal - special animation
                        events.append(AnimationEvent(
                            "geas_heal",
                            source_unit=geas_break_unit,  # Unit that had geas
                            target_unit=game_unit,  # Potpourrist healing
                            heal_amount=hp_delta
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

                # Check for death
                if current_hp <= 0:
                    events.append(AnimationEvent(
                        "death",
                        source_unit=game_unit,
                        target_unit=game_unit
                    ))

            # Detect position changes
            # NOTE: Game uses (y, x) = (row, col), we need (x, y) = (col, row)
            current_pos = (game_unit.x, game_unit.y)
            if current_pos != visual_unit.last_position:
                # Check if this position change is due to a pending teleport skill
                is_teleport = hasattr(visual_unit, 'pending_teleport_skill') and visual_unit.pending_teleport_skill
                if is_teleport:
                    print(f"[GameState] Position change is due to teleport skill {visual_unit.pending_teleport_skill}, skipping movement animation")
                    # Clear the pending teleport flag
                    visual_unit.pending_teleport_skill = None

                # Check if this is a DERELICTIONIST defection teleport (partition dissociation)
                is_defection_teleport = (hasattr(game_unit, 'pending_teleport_defection') and
                                        game_unit.pending_teleport_defection)
                if is_defection_teleport:
                    print(f"[GameState] *** DERELICTIONIST DEFECTION TELEPORT DETECTED ***")
                    origin = getattr(game_unit, 'teleport_origin', visual_unit.last_position)
                    destination = getattr(game_unit, 'teleport_destination', current_pos)
                    print(f"  Origin: {origin}, Destination: {destination}")

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

                    print(f"[GameState] Teleport position synced: grid ({game_unit.x}, {game_unit.y}) -> screen ({new_x}, {new_y})")

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

                    # FIXME: move_to_grid calculates target position without offset
                    # We need to add GRID_OFFSET manually
                    # Import at function level to avoid circular dependency
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
                    print(f"[GameState] Synced teleport position: game ({game_unit.x}, {game_unit.y}) -> visual grid ({animated_unit.grid_x}, {animated_unit.grid_y})")

            # Detect basic attack ONLY during turn execution
            # Attacks get set when planned, but we only want to animate them when executed
            if self.executing_turn:
                if hasattr(game_unit, 'attack_target') and game_unit.attack_target:
                    # Check if this is a new attack (not already animated)
                    if game_unit.attack_target != visual_unit.last_attack_target:
                        # Basic attack is being executed!
                        attack_target = game_unit.attack_target  # (y, x) in game coords

                        print(f"[GameState] Detected basic attack during turn execution: {game_unit.get_display_name()} → {attack_target}")

                        # Capture INTERFERER's carrier_rave_active state BEFORE attack execution clears it
                        # (Similar to Potpourrist infusion check below)
                        has_carrier_rave = False
                        if hasattr(game_unit, 'carrier_rave_active'):
                            has_carrier_rave = game_unit.carrier_rave_active
                            if has_carrier_rave:
                                print(f"[GameState] INTERFERER has carrier_rave_active - attack will be triple strike!")

                        events.append(AnimationEvent(
                            "attack",
                            source_unit=game_unit,
                            target_unit=None,
                            attack_target=attack_target,
                            has_carrier_rave=has_carrier_rave  # Pass flag to renderer
                        ))
                        visual_unit.last_attack_target = game_unit.attack_target
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

                        print(f"[GameState] Detected skill during turn execution: {skill_name} on {game_unit.get_display_name()}")

                        # Track if this is a teleport/movement skill that will change position
                        # These skills have their own animation and should not show walking animation
                        teleport_skills = ["Delta Config", "Vault", "Græ Exchange", "Grae Exchange", "Expedite"]
                        if skill_name in teleport_skills:
                            # Store this in visual_unit so we can check it when detecting position changes
                            visual_unit.pending_teleport_skill = skill_name
                            print(f"[GameState] Marking {skill_name} as pending movement skill")

                        # Capture Potpourrist's infusion state BEFORE skill execution clears it
                        is_infused = False
                        if skill_name in ["Demilune", "Granite Geas"] and hasattr(game_unit, 'potpourri_held'):
                            is_infused = game_unit.potpourri_held
                            if is_infused:
                                print(f"[GameState] Potpourrist is holding potpourri - {skill_name} will be infused!")

                        events.append(AnimationEvent(
                            "skill",
                            source_unit=game_unit,
                            target_unit=None,
                            skill_name=skill_name,
                            skill_target=skill_target,
                            is_infused=is_infused
                        ))
                        visual_unit.last_skill = game_unit.selected_skill
                elif visual_unit.last_skill is not None:
                    # Skill was cleared - reset our tracking
                    visual_unit.last_skill = None

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
                    print(f"[GameState] Passive skill '{passive_name}' activated for {game_unit.get_display_name()}!")

                    # Queue animation for passive skill activation
                    events.append(AnimationEvent(
                        "skill",
                        source_unit=game_unit,
                        target_unit=None,
                        skill_name=passive_name.upper(),
                        skill_target=None
                    ))

                    visual_unit.last_passive_activated = True

            # Detect trap releases (Viseroy trap)
            current_trapped_by = getattr(game_unit, 'trapped_by', None)
            if visual_unit.last_trapped_by and not current_trapped_by:
                # Unit was trapped and is now released!
                trapper_unit = visual_unit.last_trapped_by
                print(f"[GameState] *** TRAP RELEASE DETECTED! {game_unit.get_display_name()} released from {trapper_unit.get_display_name()}'s Viseroy trap ***")

                events.append(AnimationEvent(
                    "trap_release",
                    source_unit=trapper_unit,  # MANDIBLE FOREMAN who set the trap
                    target_unit=game_unit  # Unit being released
                ))

            # Update trapped_by tracking
            visual_unit.last_trapped_by = current_trapped_by

            # Update taunted units snapshot at end of each sync cycle
            # This ensures we have the "before" state for next cycle's geas heal detection
            new_taunted = visual_unit._get_taunted_units(game_unit, self.game)
            if new_taunted != visual_unit.last_taunted_units:
                print(f"[GameState] Updating {game_unit.get_display_name()} taunted snapshot: {visual_unit.last_taunted_units} -> {new_taunted}")
            visual_unit.last_taunted_units = new_taunted

        # Status effects are shown after damage numbers via _show_active_status_effects()
        # in the renderer, using _effects_to_show_after_damage populated by the callback

        # Update scalar node tracking for next sync
        if hasattr(self.game, 'scalar_nodes'):
            self.last_scalar_nodes = self.game.scalar_nodes.copy()

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

    def get_pending_animations(self) -> List[AnimationEvent]:
        """Get and clear pending animations."""
        animations = self.animation_queue.copy()
        self.animation_queue.clear()
        return animations

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

    def get_attack_range(self, game_unit) -> List[Tuple[int, int]]:
        """
        Get valid attack positions for a unit.

        Args:
            game_unit: The game logic unit

        Returns:
            List of (x, y) tuples in renderer coordinates (column, row)
        """
        if not self.game or not game_unit:
            return []

        # Get possible attacks from game (returns list of (y, x) tuples)
        possible_attacks = self.game.get_possible_attacks(game_unit)

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

        # Get skill range
        skill_range = skill.range

        # Check all positions within range
        for y in range(max(0, from_y - skill_range), min(self.game.map.height, from_y + skill_range + 1)):
            for x in range(max(0, from_x - skill_range), min(self.game.map.width, from_x + skill_range + 1)):
                # Calculate distance
                distance = self.game.chess_distance(from_y, from_x, y, x)
                if distance > skill_range:
                    continue

                # Check if skill can be used on this position
                if skill.can_use(game_unit, (y, x), self.game):
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

            # TODO: Execute skill through game logic
            # caster = self.game.get_unit(self.selected_unit_id)
            # target = self.game.get_unit(target_id)
            # result = self.game.use_skill(caster, self.selected_skill, target)

            # Queue animation
            # self.queue_skill_animation(self.selected_skill, caster, target)

            # Reset state
            self.selected_skill = None
            self.awaiting_target = False
            return True

        elif action_type == "move_unit":
            if not self.selected_unit_id:
                return False

            target_x = kwargs.get("grid_x")
            target_y = kwargs.get("grid_y")

            # TODO: Execute move through game logic
            # unit = self.game.get_unit(self.selected_unit_id)
            # result = self.game.move_unit(unit, target_x, target_y)

            return True

        elif action_type == "end_turn":
            # TODO: End turn in game logic
            # self.game.end_turn()
            return True

        return False

    def get_game_state(self) -> Dict[str, Any]:
        """
        Get current game state for UI display.

        Returns:
            Dictionary with current game state info
        """
        if not self.game:
            return {}

        return {
            "turn": self.current_turn,
            "phase": self.game_phase,
            "active_unit": self.active_unit_id,
            "selected_unit": self.selected_unit_id,
            "selected_skill": self.selected_skill,
            "awaiting_target": self.awaiting_target,
            # TODO: Add more state as needed
        }

    def get_valid_targets(self, skill_name: str, caster) -> List[Any]:
        """
        Get list of valid targets for a skill.

        Args:
            skill_name: Name of the skill
            caster: Unit casting the skill

        Returns:
            List of valid target units
        """
        # TODO: Query game logic for valid targets
        # return self.game.get_valid_targets(skill_name, caster)
        return []


    def is_game_over(self) -> bool:
        """Check if game is over."""
        # TODO: Query game logic
        # return self.game.is_game_over()
        return False

    def get_winner(self) -> Optional[str]:
        """Get winner if game is over."""
        # TODO: Query game logic
        # return self.game.get_winner()
        return None
