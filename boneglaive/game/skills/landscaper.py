#!/usr/bin/env python3
"""
Skills specific to the LANDSCAPER unit type.
This module contains all passive and active abilities for LANDSCAPER units.

The LANDSCAPER is a terrain manipulator who reshapes the battlefield through
acoustic resonance — grabbing terrain, building slag walls, turning units into
topiary sculptures, and shattering terrain for piercing shrapnel damage.
"""

try:
    import curses
except ImportError:
    curses = None
import time
from typing import Optional, List, Tuple, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


# Direction vectors for 8 directions
DIRECTION_VECTORS = {
    'N':  (-1,  0),
    'NE': (-1,  1),
    'E':  ( 0,  1),
    'SE': ( 1,  1),
    'S':  ( 1,  0),
    'SW': ( 1, -1),
    'W':  ( 0, -1),
    'NW': (-1, -1),
}

# 90° counter-clockwise rotation mapping for Hornswoggle drag direction
DRAG_DIRECTION_CCW = {
    'N':  'W',
    'NE': 'NW',
    'E':  'N',
    'SE': 'NE',
    'S':  'E',
    'SW': 'SE',
    'W':  'S',
    'NW': 'SW',
}


def _direction_from_delta(dy, dx):
    """Convert a (dy, dx) delta to a direction name string."""
    for name, (vdy, vdx) in DIRECTION_VECTORS.items():
        if vdy == dy and vdx == dx:
            return name
    return None


def _get_effective_position(user):
    """Get the position a unit will act from (move_target if planned, else current pos)."""
    if user.move_target:
        return user.move_target[0], user.move_target[1]
    return user.y, user.x


def _get_cone_tiles(origin_y, origin_x, direction, game):
    """
    Calculate tiles in the Topiary Breath cone.
    Cone shape: distance 1 = 3 wide, distance 2 = 5 wide,
    distance 3 = 7 wide, distance 4 = 7 wide.

    Returns list of (y, x) tuples within map bounds.
    """
    dy, dx = DIRECTION_VECTORS[direction]
    tiles = []

    # Width at each distance: 3, 5, 7, 7
    widths = [3, 5, 7, 7]

    # Calculate perpendicular direction for cone spread
    # Perpendicular to (dy, dx) is (-dx, dy) and (dx, -dy)
    if dy == 0:
        # Horizontal: E or W. Perpendicular is N/S
        perp_dy, perp_dx = 1, 0
    elif dx == 0:
        # Vertical: N or S. Perpendicular is E/W
        perp_dy, perp_dx = 0, 1
    else:
        # Diagonal: perpendicular directions depend on the diagonal
        # For NE (dy=-1, dx=1): perp is NW-SE axis → (dy=-1,dx=-1) and (dy=1,dx=1)
        # But for cone spread we need the cross-axis
        # For diagonal movement, spread along both perpendicular axes
        # NE/SW axis → spread along NW/SE: perp = (-1,-1) normalized per step
        # Actually for diagonals, we spread along the two adjacent cardinal directions
        # NE: spread along N and E → actually we need to fan out
        # Simplest: for diagonal, perpendicular vectors are the two cardinals
        # NE (dy=-1,dx=1): perp1 = (-1,-1) norm? No.
        # Let's use: for diagonal (dy,dx), perp = (-dx, dy) gives us the 90° CCW rotation
        perp_dy, perp_dx = -dx, dy

    for dist_idx, width in enumerate(widths):
        dist = dist_idx + 1
        # Center of this row
        center_y = origin_y + dy * dist
        center_x = origin_x + dx * dist
        half_width = width // 2

        for offset in range(-half_width, half_width + 1):
            tile_y = center_y + perp_dy * offset
            tile_x = center_x + perp_dx * offset
            if game.is_valid_position(tile_y, tile_x):
                tiles.append((tile_y, tile_x))

    return tiles


class TranslativeStroke(PassiveSkill):
    """
    Passive skill for LANDSCAPER.
    Basic attacks hit 4 times (one per tuning fork). Skill cooldowns are reduced
    by the total damage dealt across all four hits.
    """

    def __init__(self):
        super().__init__(
            name="Translative Stroke",
            key="T",
            description="Basic attacks hit 4 times. All skill cooldowns reduced by total damage dealt."
        )

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        # Handled in engine.py attack resolution — the engine checks for LANDSCAPER
        # type and performs 4 hits + cooldown reduction
        pass


class HornswoggleSkill(ActiveSkill):
    """
    Active skill: HORNSWOGGLE
    Fire a sonic wave in one of 8 directions. The wave grabs the first terrain/furniture
    it hits and drags it 90° CCW, depositing slag walls along the drag path.
    """

    WAVE_RANGE = 4
    DRAG_RANGE = 4
    SLAG_DURATION = 3

    def __init__(self):
        super().__init__(
            name="Hornswoggle",
            key="H",
            description="Fire sonic wave to grab terrain, drag it 90° CCW depositing slag walls. Wave range 3, drag range 4.",
            target_type=TargetType.NONE,
            cooldown=4,
            range_=0
        )
        # Stored during use() for execute()
        self.fire_direction = None

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        source_y, source_x = _get_effective_position(user)
        # Check if there's any terrain within wave range in any direction
        for dir_name, (dy, dx) in DIRECTION_VECTORS.items():
            for dist in range(1, self.WAVE_RANGE + 1):
                check_y = source_y + dy * dist
                check_x = source_x + dx * dist
                if not game.is_valid_position(check_y, check_x):
                    break
                # Units block the wave UNLESS they are topiaries (topiaries are terrain)
                unit_at = game.get_unit_at(check_y, check_x)
                if unit_at:
                    if hasattr(unit_at, 'is_topiary') and unit_at.is_topiary:
                        return True  # Topiary is valid terrain to grab
                    else:
                        break  # Normal unit blocks wave
                if not game.map.is_passable(check_y, check_x) or game.map.is_furniture(check_y, check_x):
                    return True
        return False

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Queue Hornswoggle. target_pos encodes direction as adjacent tile from effective position."""
        if not self.can_use(user, target_pos, game):
            return False

        if not target_pos:
            return False

        source_y, source_x = _get_effective_position(user)

        # target_pos is an adjacent tile — derive direction from effective position
        dy = target_pos[0] - source_y
        dx = target_pos[1] - source_x

        # Normalize to unit direction
        if dy != 0:
            dy = 1 if dy > 0 else -1
        if dx != 0:
            dx = 1 if dx > 0 else -1

        direction = _direction_from_delta(dy, dx)
        if not direction:
            return False

        # Validate: there must be terrain in this direction within wave range
        grab_pos = self._find_terrain_in_direction(source_y, source_x, direction, game)
        if not grab_pos:
            return False

        # Store direction and source position for execute phase
        self.fire_direction = direction
        self.fire_source = (source_y, source_x)

        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown

        message_log.add_message(
            f"{user.get_display_name()} aims the horn array {direction}",
            MessageType.ABILITY,
            player=user.player
        )

        logger.info(f"HORNSWOGGLE QUEUED: {user.get_display_name()} firing {direction} from ({source_y},{source_x})")
        return True

    def _find_terrain_in_direction(self, from_y, from_x, direction, game):
        """Find the first terrain tile in the given direction within wave range.
        Topiary-units count as terrain (grabbable). Normal units block the wave."""
        dy, dx = DIRECTION_VECTORS[direction]
        for dist in range(1, self.WAVE_RANGE + 1):
            check_y = from_y + dy * dist
            check_x = from_x + dx * dist
            if not game.is_valid_position(check_y, check_x):
                return None
            # Check for units — topiaries are terrain, others block
            unit_at = game.get_unit_at(check_y, check_x)
            if unit_at:
                if hasattr(unit_at, 'is_topiary') and unit_at.is_topiary:
                    return (check_y, check_x)  # Topiary is grabbable terrain
                else:
                    return None  # Normal unit blocks wave
            # Check for any non-passable terrain or furniture
            if not game.map.is_passable(check_y, check_x) or game.map.is_furniture(check_y, check_x):
                return (check_y, check_x)
        return None

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Hornswoggle during combat phase."""
        from boneglaive.game.map import TerrainType

        direction = self.fire_direction
        if not direction:
            logger.warning("HORNSWOGGLE: No direction stored")
            return

        # Use stored source position (calculated during planning from effective position)
        source_y, source_x = getattr(self, 'fire_source', (user.y, user.x))

        # Find terrain in wave path from the source position
        grab_pos = self._find_terrain_in_direction(source_y, source_x, direction, game)
        if not grab_pos:
            message_log.add_message(
                f"{user.get_display_name()}'s sonic wave finds nothing to grab",
                MessageType.ABILITY,
                player=user.player
            )
            return

        grab_y, grab_x = grab_pos
        grabbed_terrain = game.map.get_terrain_at(grab_y, grab_x)

        # Check if we're grabbing a topiary-unit
        grabbed_topiary_unit = None
        unit_at_grab = game.get_unit_at(grab_y, grab_x)
        if unit_at_grab and hasattr(unit_at_grab, 'is_topiary') and unit_at_grab.is_topiary:
            grabbed_topiary_unit = unit_at_grab

        # Show wave animation (text mode)
        if ui and hasattr(ui, 'renderer'):
            from boneglaive.utils.animation_helpers import sleep_with_animation_speed
            dy, dx = DIRECTION_VECTORS[direction]
            wave_frames = ['~', '=', '>']
            for dist in range(1, self.WAVE_RANGE + 1):
                wave_y = source_y + dy * dist
                wave_x = source_x + dx * dist
                if not game.is_valid_position(wave_y, wave_x):
                    break
                if (wave_y, wave_x) == grab_pos:
                    # Grab impact
                    for frame in ['*', '#', '!']:
                        ui.renderer.draw_damage_text(wave_y, wave_x * 2, frame, 6)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.06)
                    break
                frame = wave_frames[dist % len(wave_frames)]
                ui.renderer.draw_damage_text(wave_y, wave_x * 2, frame, 6)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)

        # Remove terrain from original position
        game.map.set_terrain_at(grab_y, grab_x, TerrainType.EMPTY)

        # If topiary-unit, also remove from topiary tracking at old position
        if grabbed_topiary_unit:
            if hasattr(game, 'topiary_units') and (grab_y, grab_x) in game.topiary_units:
                del game.topiary_units[(grab_y, grab_x)]

        grab_name = grabbed_topiary_unit.get_display_name() if grabbed_topiary_unit else grabbed_terrain.name.replace('_', ' ').lower()
        message_log.add_message(
            f"Sonic wave rips {grab_name} from ({grab_y},{grab_x})",
            MessageType.ABILITY,
            player=user.player
        )

        # Calculate drag direction (90° CCW)
        drag_dir_name = DRAG_DIRECTION_CCW[direction]
        drag_dy, drag_dx = DIRECTION_VECTORS[drag_dir_name]

        # Track slag wall data for duration management
        if not hasattr(game, 'slag_wall_tiles'):
            game.slag_wall_tiles = {}

        # Build the full drag path — terrain flies over everything, slag forces into each tile
        # Slag displaces existing terrain and units along the path
        slag_positions = []
        drag_tiles = []

        # First tile is the grab point itself
        drag_tiles.append((grab_y, grab_x))

        # Then each step along the drag direction
        for dist in range(1, self.DRAG_RANGE + 1):
            tile_y = grab_y + drag_dy * dist
            tile_x = grab_x + drag_dx * dist
            if not game.is_valid_position(tile_y, tile_x):
                break
            drag_tiles.append((tile_y, tile_x))

        # The terrain deposits at the last valid tile in the path
        # Slag goes on every tile EXCEPT the deposit tile
        deposit_y, deposit_x = drag_tiles[-1]

        # Process each tile along the path (except the deposit tile) — place slag
        for slag_y, slag_x in drag_tiles[:-1]:
            # Displace any unit at this position
            displaced_unit = game.get_unit_at(slag_y, slag_x)
            if displaced_unit and displaced_unit != grabbed_topiary_unit:
                # Find adjacent empty passable tile to push unit to
                displaced = False
                for ddy in [-1, 0, 1]:
                    for ddx in [-1, 0, 1]:
                        if ddy == 0 and ddx == 0:
                            continue
                        push_y = slag_y + ddy
                        push_x = slag_x + ddx
                        if (game.is_valid_position(push_y, push_x) and
                                game.map.is_passable(push_y, push_x) and
                                game.get_unit_at(push_y, push_x) is None and
                                (push_y, push_x) not in drag_tiles):
                            old_dy, old_dx = displaced_unit.y, displaced_unit.x
                            displaced_unit.y = push_y
                            displaced_unit.x = push_x
                            game._update_unit_grid(displaced_unit, old_dy, old_dx)
                            message_log.add_message(
                                f"{displaced_unit.get_display_name()} is displaced by molten slag",
                                MessageType.WARNING,
                                player=user.player
                            )
                            displaced = True
                            break
                    if displaced:
                        break

            # Place slag wall — overwrites whatever terrain was here
            game.map.set_terrain_at(slag_y, slag_x, TerrainType.SLAG_WALL)
            game.slag_wall_tiles[(slag_y, slag_x)] = {
                'duration': self.SLAG_DURATION,
                'owner': user
            }
            slag_positions.append((slag_y, slag_x))

            # Show slag forming animation
            if ui and hasattr(ui, 'renderer'):
                from boneglaive.utils.animation_helpers import sleep_with_animation_speed
                for frame in ['~', '=', '#']:
                    ui.renderer.draw_damage_text(slag_y, slag_x * 2, frame, 1)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.04)

        # Process deposit tile — displace any unit there too
        deposit_unit = game.get_unit_at(deposit_y, deposit_x)
        if deposit_unit and deposit_unit != grabbed_topiary_unit:
            displaced = False
            for ddy in [-1, 0, 1]:
                for ddx in [-1, 0, 1]:
                    if ddy == 0 and ddx == 0:
                        continue
                    push_y = deposit_y + ddy
                    push_x = deposit_x + ddx
                    if (game.is_valid_position(push_y, push_x) and
                            game.map.is_passable(push_y, push_x) and
                            game.get_unit_at(push_y, push_x) is None and
                            (push_y, push_x) not in drag_tiles):
                        old_dy, old_dx = deposit_unit.y, deposit_unit.x
                        deposit_unit.y = push_y
                        deposit_unit.x = push_x
                        game._update_unit_grid(deposit_unit, old_dy, old_dx)
                        message_log.add_message(
                            f"{deposit_unit.get_display_name()} is displaced by falling terrain",
                            MessageType.WARNING,
                            player=user.player
                        )
                        displaced = True
                        break
                if displaced:
                    break

        # Deposit grabbed terrain at final position
        game.map.set_terrain_at(deposit_y, deposit_x, grabbed_terrain)

        # If we grabbed a topiary-unit, move the unit to the deposit position
        if grabbed_topiary_unit:
            old_y, old_x = grabbed_topiary_unit.y, grabbed_topiary_unit.x
            grabbed_topiary_unit.y = deposit_y
            grabbed_topiary_unit.x = deposit_x
            game._update_unit_grid(grabbed_topiary_unit, old_y, old_x)

            # Re-register in topiary tracking at new position
            game.topiary_units[(deposit_y, deposit_x)] = {
                'unit': grabbed_topiary_unit,
                'duration': grabbed_topiary_unit.topiary_duration,
                'original_terrain': TerrainType.EMPTY
            }

            message_log.add_message(
                f"{grabbed_topiary_unit.get_display_name()} dragged to ({deposit_y},{deposit_x})",
                MessageType.WARNING,
                player=user.player
            )

        message_log.add_message(
            f"Terrain deposited at ({deposit_y},{deposit_x}), {len(slag_positions)} slag walls created",
            MessageType.ABILITY,
            player=user.player
        )

        logger.info(f"HORNSWOGGLE EXECUTED: {user.get_display_name()} grabbed "
                     f"{'topiary ' + grabbed_topiary_unit.get_display_name() if grabbed_topiary_unit else grabbed_terrain.name} "
                     f"from ({grab_y},{grab_x}), dragged {drag_dir_name}, "
                     f"{len(slag_positions)} slag walls, deposited at ({deposit_y},{deposit_x})")

        # Store execution data for graphical animation to read
        user.last_hornswoggle_data = {
            'source': (source_y, source_x),
            'direction': direction,
            'grab_pos': (grab_y, grab_x),
            'drag_direction': drag_dir_name,
            'slag_positions': list(slag_positions),
            'deposit_pos': (deposit_y, deposit_x),
            'grabbed_terrain': grabbed_terrain,
            'grabbed_topiary': grabbed_topiary_unit is not None,
        }

        self.fire_direction = None
        self.fire_source = None


class TopiaryBreathSkill(ActiveSkill):
    """
    Active skill: TOPIARY BREATH
    Blast a cone of petrifying resonance that transforms all units (allies and enemies)
    into topiary terrain sculptures. Units are rearranged into a checker pattern.
    Lasts 1 turn.
    """

    def __init__(self):
        super().__init__(
            name="Topiary Breath",
            key="B",
            description="Cone blast transforms all units into terrain topiaries for 1 turn. Rearranges into checker pattern. Affects allies too!",
            target_type=TargetType.NONE,
            cooldown=8,
            range_=0
        )
        self.fire_direction = None

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        # Check if there are any units in any possible cone direction
        source_y, source_x = _get_effective_position(user)
        for dir_name in DIRECTION_VECTORS:
            cone_tiles = _get_cone_tiles(source_y, source_x, dir_name, game)
            for ty, tx in cone_tiles:
                unit_at = game.get_unit_at(ty, tx)
                if unit_at and unit_at != user and unit_at.is_alive():
                    return True
        return False

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False

        if not target_pos:
            return False

        source_y, source_x = _get_effective_position(user)

        # Derive direction from effective position
        dy = target_pos[0] - source_y
        dx = target_pos[1] - source_x
        if dy != 0:
            dy = 1 if dy > 0 else -1
        if dx != 0:
            dx = 1 if dx > 0 else -1

        direction = _direction_from_delta(dy, dx)
        if not direction:
            return False

        self.fire_direction = direction
        self.fire_source = (source_y, source_x)

        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown

        message_log.add_message(
            f"{user.get_display_name()} breathes petrifying resonance {direction}",
            MessageType.ABILITY,
            player=user.player
        )

        logger.info(f"TOPIARY BREATH QUEUED: {user.get_display_name()} firing {direction}")
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Topiary Breath during combat phase."""
        from boneglaive.game.map import TerrainType

        direction = self.fire_direction
        if not direction:
            logger.warning("TOPIARY BREATH: No direction stored")
            return

        source_y, source_x = getattr(self, 'fire_source', (user.y, user.x))
        cone_tiles = _get_cone_tiles(source_y, source_x, direction, game)

        # Find all units in the cone (excluding the caster)
        caught_units = []
        for ty, tx in cone_tiles:
            unit_at = game.get_unit_at(ty, tx)
            if unit_at and unit_at != user and unit_at.is_alive():
                # Check immunity
                if unit_at.is_immune_to_effects():
                    message_log.add_message(
                        f"{unit_at.get_display_name()} resists Topiary Breath due to Stasiality",
                        MessageType.ABILITY,
                        player=unit_at.player
                    )
                    continue
                caught_units.append(unit_at)

        if not caught_units:
            message_log.add_message(
                f"{user.get_display_name()}'s Topiary Breath catches no one",
                MessageType.ABILITY,
                player=user.player
            )
            self.fire_direction = None
            return

        # Generate checker pattern positions within the cone
        checker_positions = []
        for i, (ty, tx) in enumerate(cone_tiles):
            # Checker: only use positions where (ty + tx) is even
            if (ty + tx) % 2 == 0:
                # Must be empty and passable, and no unit already placed there
                if (game.map.is_passable(ty, tx) and
                        game.get_unit_at(ty, tx) is None and
                        (ty, tx) not in [(u.y, u.x) for u in caught_units]):
                    checker_positions.append((ty, tx))

        # If not enough checker positions, also use odd positions
        if len(checker_positions) < len(caught_units):
            for ty, tx in cone_tiles:
                if (ty + tx) % 2 != 0:
                    if (game.map.is_passable(ty, tx) and
                            game.get_unit_at(ty, tx) is None):
                        checker_positions.append((ty, tx))
                if len(checker_positions) >= len(caught_units):
                    break

        # Initialize topiary tracking on game
        if not hasattr(game, 'topiary_units'):
            game.topiary_units = {}

        # Transform each caught unit
        units_transformed = 0
        for i, unit in enumerate(caught_units):
            # Move to checker position if available
            if i < len(checker_positions):
                new_y, new_x = checker_positions[i]
                old_y, old_x = unit.y, unit.x
                unit.y = new_y
                unit.x = new_x
                game._update_unit_grid(unit, old_y, old_x)
            # else unit stays in place

            # Mark unit as topiary
            unit.is_topiary = True
            unit.topiary_duration = 2

            # Grant 999 PRT (invulnerable while terrain) and store original
            unit.topiary_original_prt = unit.prt
            unit.prt = 999

            # Place TOPIARY terrain at unit's position
            game.map.set_terrain_at(unit.y, unit.x, TerrainType.TOPIARY)

            # Track for revert
            game.topiary_units[(unit.y, unit.x)] = {
                'unit': unit,
                'duration': 2,
                'original_terrain': TerrainType.EMPTY
            }

            units_transformed += 1

            message_log.add_message(
                f"{unit.get_display_name()} is sculpted into a topiary at ({unit.y},{unit.x})",
                MessageType.WARNING,
                player=user.player
            )

            # Text mode transform animation
            if ui and hasattr(ui, 'renderer'):
                from boneglaive.utils.animation_helpers import sleep_with_animation_speed
                for frame in ['@', '%', '&', '&']:
                    ui.renderer.draw_damage_text(unit.y, unit.x * 2, frame, 2)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.06)

        message_log.add_message(
            f"Topiary Breath transforms {units_transformed} unit(s) into garden sculptures",
            MessageType.ABILITY,
            player=user.player
        )

        logger.info(f"TOPIARY BREATH EXECUTED: {user.get_display_name()} transformed "
                     f"{units_transformed} units in {direction} cone")

        # Store execution data for graphical animation to read
        user.last_topiary_breath_data = {
            'source': (source_y, source_x),
            'direction': direction,
            'cone_tiles': list(cone_tiles),
            'transformed_units': [(u.y, u.x) for u in caught_units[:units_transformed]],
        }

        self.fire_direction = None
        self.fire_source = None


class DissonanceSkill(ActiveSkill):
    """
    Active skill: DISSONANCE
    Launch an acoustic gyre into terrain, shattering it from within.
    Shrapnel flies in all 8 directions dealing piercing damage.
    Shrapnel stops at terrain, passes through units.
    """

    SHRAPNEL_RANGE = 2

    def __init__(self):
        super().__init__(
            name="Dissonance",
            key="D",
            description="Launch acoustic gyre to shatter terrain. 4 piercing shrapnel in 8 directions. Stops at terrain, passes through units. Frees topiary units.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=4
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False

        source_y, source_x = _get_effective_position(user)

        if target_pos:
            # Specific target — must be within range and be terrain
            ty, tx = target_pos
            dist = game.chess_distance(source_y, source_x, ty, tx)
            if dist > self.range:
                return False
            # Must be non-passable terrain, furniture, or topiary
            is_terrain = not game.map.is_passable(ty, tx) or game.map.is_furniture(ty, tx)
            is_topiary = hasattr(game, 'topiary_units') and (ty, tx) in game.topiary_units
            if not is_terrain and not is_topiary:
                return False
            return True
        else:
            # General check — is there any terrain within cast range?
            for y in range(source_y - self.range, source_y + self.range + 1):
                for x in range(source_x - self.range, source_x + self.range + 1):
                    if not game.is_valid_position(y, x):
                        continue
                    if game.chess_distance(source_y, source_x, y, x) > self.range:
                        continue
                    if not game.map.is_passable(y, x) or game.map.is_furniture(y, x):
                        return True
                    if hasattr(game, 'topiary_units') and (y, x) in game.topiary_units:
                        return True
            return False

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown

        message_log.add_message(
            f"{user.get_display_name()} prepares to shatter terrain at ({target_pos[0]},{target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )

        logger.info(f"DISSONANCE QUEUED: {user.get_display_name()} targeting ({target_pos[0]},{target_pos[1]})")
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Dissonance during combat phase."""
        from boneglaive.game.map import TerrainType

        ty, tx = target_pos

        # Check if target is still terrain (might have been moved/destroyed)
        terrain_at = game.map.get_terrain_at(ty, tx)
        if game.map.is_passable(ty, tx) and not game.map.is_furniture(ty, tx):
            # Check if it's a topiary
            if not (hasattr(game, 'topiary_units') and (ty, tx) in game.topiary_units):
                message_log.add_message(
                    f"Target terrain at ({ty},{tx}) is gone",
                    MessageType.ABILITY,
                    player=user.player
                )
                return

        # Flat piercing damage values
        shrapnel_damage = 4  # AoE shrapnel

        # Check if shattering a topiary-unit
        topiary_unit = None
        if hasattr(game, 'topiary_units') and (ty, tx) in game.topiary_units:
            topiary_data = game.topiary_units[(ty, tx)]
            topiary_unit = topiary_data['unit']

        # Shatter the terrain
        game.map.set_terrain_at(ty, tx, TerrainType.EMPTY)

        # Clean up slag wall tracking if applicable
        if hasattr(game, 'slag_wall_tiles') and (ty, tx) in game.slag_wall_tiles:
            del game.slag_wall_tiles[(ty, tx)]

        # Text mode shatter animation — forks strike then terrain explodes
        if ui and hasattr(ui, 'renderer'):
            from boneglaive.utils.animation_helpers import sleep_with_animation_speed
            for frame in ['Y', 'Y', '!', '#', 'X', '*', '+', '.']:
                ui.renderer.draw_damage_text(ty, tx * 2, frame, 1)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)

        shattered_name = terrain_at.name.replace('_', ' ').lower()
        message_log.add_message(
            f"{user.get_display_name()} shatters {shattered_name} at ({ty},{tx})!",
            MessageType.ABILITY,
            player=user.player
        )

        # If topiary-unit: revert topiary state (unit is freed, no direct damage)
        if topiary_unit and topiary_unit.is_alive():
            topiary_unit.is_topiary = False
            topiary_unit.topiary_duration = 0

            # Restore original PRT
            if hasattr(topiary_unit, 'topiary_original_prt'):
                topiary_unit.prt = topiary_unit.topiary_original_prt
                delattr(topiary_unit, 'topiary_original_prt')

            if (ty, tx) in game.topiary_units:
                del game.topiary_units[(ty, tx)]

            message_log.add_message(
                f"{topiary_unit.get_display_name()} is freed from topiary!",
                MessageType.ABILITY,
                player=user.player
            )

        # Fire shrapnel in all 8 directions
        total_hits = 0
        for dir_name, (sdy, sdx) in DIRECTION_VECTORS.items():
            for dist in range(1, self.SHRAPNEL_RANGE + 1):
                shrap_y = ty + sdy * dist
                shrap_x = tx + sdx * dist

                if not game.is_valid_position(shrap_y, shrap_x):
                    break

                # Stop at terrain (shrapnel blocked by walls)
                if not game.map.is_passable(shrap_y, shrap_x):
                    break

                # Hit units (passes through — hits multiple)
                hit_unit = game.get_unit_at(shrap_y, shrap_x)
                if hit_unit and hit_unit.is_alive() and hit_unit != user:
                    # Friendly topiary units are protected from friendly Dissonance shrapnel
                    if hit_unit.player == user.player and getattr(hit_unit, 'is_topiary', False):
                        continue
                    old_hp = hit_unit.hp
                    actual_damage = hit_unit.deal_damage(shrapnel_damage, can_kill=True)
                    total_hits += 1

                    message_log.add_message(
                        f"Shrapnel hits {hit_unit.get_display_name()} for #DAMAGE_{actual_damage}# piercing!",
                        MessageType.WARNING,
                        player=hit_unit.player
                    )

                    # Text mode shrapnel hit animation
                    if ui and hasattr(ui, 'renderer'):
                        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
                        for frame in ['*', '+', str(actual_damage)]:
                            ui.renderer.draw_damage_text(shrap_y, shrap_x * 2, frame, 1)
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.04)

                    # Check for death
                    if hit_unit.hp <= 0 and old_hp > 0:
                        game.handle_unit_death(hit_unit, user, cause="dissonance_shrapnel", ui=ui)

                    # Check for critical health
                    game.check_critical_health(hit_unit, user, old_hp, ui)

        if total_hits > 0:
            message_log.add_message(
                f"Dissonance shrapnel hits {total_hits} unit(s) for {shrapnel_damage} piercing each",
                MessageType.ABILITY,
                player=user.player
            )

        # Store execution data for graphical animation to read
        user.last_dissonance_data = {
            'target_pos': (ty, tx),
            'was_topiary': topiary_unit is not None,
        }

        logger.info(f"DISSONANCE EXECUTED: {user.get_display_name()} shattered {shattered_name} "
                     f"at ({ty},{tx}), {total_hits} shrapnel hits for {shrapnel_damage} each")
