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

# CCW rotation for the 3x3 ring around Dissonance impact (upgrade)
# Each (dy, dx) offset maps to its CCW neighbor
RING_CCW = {
    (-1,  0): (-1, -1),   # N  → NW
    (-1, -1): ( 0, -1),   # NW → W
    ( 0, -1): ( 1, -1),   # W  → SW
    ( 1, -1): ( 1,  0),   # SW → S
    ( 1,  0): ( 1,  1),   # S  → SE
    ( 1,  1): ( 0,  1),   # SE → E
    ( 0,  1): (-1,  1),   # E  → NE
    (-1,  1): (-1,  0),   # NE → N
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

    Cardinal directions: rows of 3/5/7/7 tiles wide using a single perpendicular axis.
    Diagonal directions: diamond-shaped rows using both adjacent cardinal axes,
    with spreads of 1/1/2/2 (Manhattan distance from center).

    Returns list of (y, x) tuples within map bounds.
    """
    dy, dx = DIRECTION_VECTORS[direction]
    seen = set()
    tiles = []

    is_diagonal = dy != 0 and dx != 0

    if is_diagonal:
        # Diagonal: spread as 2D diamonds along both adjacent cardinal axes
        # NE(-1,1): vertical=(-1,0), horizontal=(0,1)
        # NW(-1,-1): vertical=(-1,0), horizontal=(0,-1)
        # SE(1,1): vertical=(1,0), horizontal=(0,1)
        # SW(1,-1): vertical=(1,0), horizontal=(0,-1)
        perp1_dy, perp1_dx = dy, 0   # vertical cardinal component
        perp2_dy, perp2_dx = 0, dx   # horizontal cardinal component
        spreads = [1, 1, 2, 2]

        for dist_idx, spread in enumerate(spreads):
            dist = dist_idx + 1
            center_y = origin_y + dy * dist
            center_x = origin_x + dx * dist
            for a in range(-spread, spread + 1):
                for b in range(-spread, spread + 1):
                    if abs(a) + abs(b) <= spread:
                        tile_y = center_y + perp1_dy * a + perp2_dy * b
                        tile_x = center_x + perp1_dx * a + perp2_dx * b
                        if game.is_valid_position(tile_y, tile_x) and (tile_y, tile_x) not in seen:
                            seen.add((tile_y, tile_x))
                            tiles.append((tile_y, tile_x))
    else:
        # Cardinal: single perpendicular axis, rows of 3/5/7/7
        if dy == 0:
            perp_dy, perp_dx = 1, 0
        else:
            perp_dy, perp_dx = 0, 1
        widths = [3, 5, 7, 7]

        for dist_idx, width in enumerate(widths):
            dist = dist_idx + 1
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
            cooldown=9,
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
            f"{user.get_display_name()} prepares to fire a sonic wave {direction}",
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
                f"{user.get_display_name()}'s sonic wave dissipates without finding terrain",
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

        # If terrain-topiary (upgraded Topiary Breath), remove from tracking
        # Once grabbed, it becomes untracked TOPIARY terrain at deposit
        if hasattr(game, 'topiary_terrain') and (grab_y, grab_x) in game.topiary_terrain:
            del game.topiary_terrain[(grab_y, grab_x)]

        grab_name = grabbed_topiary_unit.get_display_name() if grabbed_topiary_unit else grabbed_terrain.name.replace('_', ' ').lower()
        message_log.add_message(
            f"{user.get_display_name()}'s sonic wave latches onto {grab_name}",
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
            # Clean up terrain-topiary tracking if overwriting one
            if hasattr(game, 'topiary_terrain') and (slag_y, slag_x) in game.topiary_terrain:
                del game.topiary_terrain[(slag_y, slag_x)]
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
                f"{grabbed_topiary_unit.get_display_name()} is dragged to ({deposit_y},{deposit_x})",
                MessageType.WARNING,
                player=user.player
            )

        message_log.add_message(
            f"Terrain deposited at ({deposit_y},{deposit_x}), slag hardens along the drag path",
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
            cooldown=13,
            range_=0
        )
        self.fire_direction = None

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Topiary Breath")
        # Check if there are any units in any possible cone direction
        source_y, source_x = _get_effective_position(user)
        for dir_name in DIRECTION_VECTORS:
            cone_tiles = _get_cone_tiles(source_y, source_x, dir_name, game)
            for ty, tx in cone_tiles:
                unit_at = game.get_unit_at(ty, tx)
                if unit_at and unit_at != user and unit_at.is_alive():
                    return True
                # Upgraded: terrain/furniture in cone is also a valid reason to cast
                if is_upgraded and (not game.map.is_passable(ty, tx) or game.map.is_furniture(ty, tx)):
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
            f"{user.get_display_name()} prepares to unleash petrifying resonance {direction}",
            MessageType.ABILITY,
            player=user.player
        )

        logger.info(f"TOPIARY BREATH QUEUED: {user.get_display_name()} firing {direction}")
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Execute Topiary Breath during combat phase."""
        from boneglaive.game.map import TerrainType
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Topiary Breath")

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

        if not caught_units and not is_upgraded:
            message_log.add_message(
                f"{user.get_display_name()}'s petrifying resonance finds no targets",
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
        if not hasattr(game, 'topiary_terrain'):
            game.topiary_terrain = {}

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

        if units_transformed > 0:
            message_log.add_message(
                f"Petrifying resonance transforms {units_transformed} units into garden sculptures",
                MessageType.ABILITY,
                player=user.player
            )

        # Upgraded: relocate terrain/furniture to checker spots, then fill remaining with generated
        terrain_topiary_positions = []
        generated_topiary_positions = []
        checker_idx = units_transformed  # Next available checker position

        if is_upgraded:
            # Phase 1: Collect terrain/furniture tiles in cone, relocate to checker positions
            terrain_tiles = []
            for ty, tx in cone_tiles:
                # Skip positions now occupied by unit-topiaries
                if (ty, tx) in game.topiary_units:
                    continue
                if game.map.get_terrain_at(ty, tx) == TerrainType.TOPIARY:
                    continue
                if not game.map.is_passable(ty, tx) or game.map.is_furniture(ty, tx):
                    terrain_tiles.append((ty, tx))

            for ty, tx in terrain_tiles:
                if checker_idx >= len(checker_positions):
                    break  # No more checker spots — stop transforming
                dest_y, dest_x = checker_positions[checker_idx]
                checker_idx += 1

                original_terrain = game.map.get_terrain_at(ty, tx)
                # Clear original position
                game.map.set_terrain_at(ty, tx, TerrainType.EMPTY)
                # Also clean up any other tracking at the source
                if hasattr(game, 'slag_wall_tiles') and (ty, tx) in game.slag_wall_tiles:
                    del game.slag_wall_tiles[(ty, tx)]

                # Place topiary at destination
                game.map.set_terrain_at(dest_y, dest_x, TerrainType.TOPIARY)
                game.topiary_terrain[(dest_y, dest_x)] = {
                    'duration': 2,
                    'original_terrain': original_terrain,
                    'owner': user
                }
                terrain_topiary_positions.append((dest_y, dest_x))

                message_log.add_message(
                    f"{original_terrain.name.replace('_', ' ').lower()} is sculpted into a topiary",
                    MessageType.ABILITY,
                    player=user.player
                )

            # Phase 2: Fill remaining checker positions with generated topiaries
            while checker_idx < len(checker_positions):
                dest_y, dest_x = checker_positions[checker_idx]
                checker_idx += 1
                # Verify still empty (could have changed during terrain relocation)
                if (game.map.is_passable(dest_y, dest_x) and
                        game.get_unit_at(dest_y, dest_x) is None and
                        (dest_y, dest_x) not in game.topiary_units and
                        (dest_y, dest_x) not in game.topiary_terrain):
                    game.map.set_terrain_at(dest_y, dest_x, TerrainType.TOPIARY)
                    game.topiary_terrain[(dest_y, dest_x)] = {
                        'duration': 2,
                        'original_terrain': None,
                        'owner': user
                    }
                    generated_topiary_positions.append((dest_y, dest_x))

            total_new = len(terrain_topiary_positions) + len(generated_topiary_positions)
            if total_new > 0:
                message_log.add_message(
                    f"The cone erupts with {total_new} additional topiary sculptures",
                    MessageType.ABILITY,
                    player=user.player
                )

            # Text mode animation for new topiaries
            if ui and hasattr(ui, 'renderer'):
                from boneglaive.utils.animation_helpers import sleep_with_animation_speed
                for ny, nx in terrain_topiary_positions + generated_topiary_positions:
                    for frame in ['~', '%', '&']:
                        ui.renderer.draw_damage_text(ny, nx * 2, frame, 2)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.03)

        logger.info(f"TOPIARY BREATH EXECUTED: {user.get_display_name()} transformed "
                     f"{units_transformed} units, {len(terrain_topiary_positions)} terrain, "
                     f"{len(generated_topiary_positions)} generated in {direction} cone")

        # Store execution data for graphical animation to read
        user.last_topiary_breath_data = {
            'source': (source_y, source_x),
            'direction': direction,
            'cone_tiles': list(cone_tiles),
            'transformed_units': [(u.y, u.x) for u in caught_units[:units_transformed]],
            'terrain_topiaries': terrain_topiary_positions,
            'generated_topiaries': generated_topiary_positions,
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
            description="Launch acoustic gyre to shatter terrain. 5 piercing shrapnel in 8 directions. Stops at terrain, passes through units. Frees topiary units.",
            target_type=TargetType.AREA,
            cooldown=9,
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
            f"{user.get_display_name()} prepares to shatter terrain",
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
                    f"The target terrain has already been destroyed",
                    MessageType.ABILITY,
                    player=user.player
                )
                return

        # Flat piercing damage values
        shrapnel_damage = 5  # AoE shrapnel

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

        # Clean up terrain-topiary tracking if applicable (upgraded Topiary Breath)
        if hasattr(game, 'topiary_terrain') and (ty, tx) in game.topiary_terrain:
            del game.topiary_terrain[(ty, tx)]

        # Text mode shatter animation — forks strike then terrain explodes
        if ui and hasattr(ui, 'renderer'):
            from boneglaive.utils.animation_helpers import sleep_with_animation_speed
            for frame in ['Y', 'Y', '!', '#', 'X', '*', '+', '.']:
                ui.renderer.draw_damage_text(ty, tx * 2, frame, 1)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)

        shattered_name = terrain_at.name.replace('_', ' ').lower()
        message_log.add_message(
            f"{user.get_display_name()} shatters the {shattered_name}!",
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
                    # Shrapnel doesn't hit allies
                    if hit_unit.player == user.player:
                        continue
                    old_hp = hit_unit.hp
                    actual_damage = hit_unit.deal_damage(shrapnel_damage, can_kill=True)
                    total_hits += 1

                    message_log.add_message(
                        f"Shrapnel pierces {hit_unit.get_display_name()} for #DAMAGE_{actual_damage}# damage!",
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
                f"Shrapnel tears through {total_hits} units",
                MessageType.ABILITY,
                player=user.player
            )

        # Upgraded: CCW terrain rotation in 3x3 ring around impact
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Dissonance")
        rotated_tiles = []

        if is_upgraded:
            # Snapshot all 8 ring positions before any changes
            ring_snapshot = {}
            for (dy, dx) in RING_CCW:
                ry, rx = ty + dy, tx + dx
                if not game.is_valid_position(ry, rx):
                    ring_snapshot[(dy, dx)] = None
                    continue

                terrain = game.map.get_terrain_at(ry, rx)

                # Only rotate non-passable terrain and furniture (not floor textures)
                is_terrain = not game.map.is_passable(ry, rx)
                is_furn = game.map.is_furniture(ry, rx)
                if terrain == TerrainType.EMPTY or (not is_terrain and not is_furn):
                    ring_snapshot[(dy, dx)] = None
                    continue

                slag_data = None
                topiary_terrain_data = None
                topiary_unit_data = None

                if hasattr(game, 'slag_wall_tiles') and (ry, rx) in game.slag_wall_tiles:
                    slag_data = game.slag_wall_tiles[(ry, rx)].copy()
                if hasattr(game, 'topiary_terrain') and (ry, rx) in game.topiary_terrain:
                    topiary_terrain_data = game.topiary_terrain[(ry, rx)].copy()
                if hasattr(game, 'topiary_units') and (ry, rx) in game.topiary_units:
                    topiary_unit_data = game.topiary_units[(ry, rx)].copy()

                ring_snapshot[(dy, dx)] = {
                    'pos': (ry, rx),
                    'terrain': terrain,
                    'slag': slag_data,
                    'topiary_terrain': topiary_terrain_data,
                    'topiary_unit': topiary_unit_data,
                }

            # Clear all source positions
            for (dy, dx), snap in ring_snapshot.items():
                if snap is None:
                    continue
                ry, rx = snap['pos']
                game.map.set_terrain_at(ry, rx, TerrainType.EMPTY)
                if hasattr(game, 'slag_wall_tiles') and (ry, rx) in game.slag_wall_tiles:
                    del game.slag_wall_tiles[(ry, rx)]
                if hasattr(game, 'topiary_terrain') and (ry, rx) in game.topiary_terrain:
                    del game.topiary_terrain[(ry, rx)]
                if hasattr(game, 'topiary_units') and (ry, rx) in game.topiary_units:
                    del game.topiary_units[(ry, rx)]

            # Place terrain at CCW destinations
            units_to_displace = []
            for (src_dy, src_dx), (dest_dy, dest_dx) in RING_CCW.items():
                snap = ring_snapshot[(src_dy, src_dx)]
                if snap is None:
                    continue

                dest_y = ty + dest_dy
                dest_x = tx + dest_dx
                if not game.is_valid_position(dest_y, dest_x):
                    continue

                terrain = snap['terrain']
                game.map.set_terrain_at(dest_y, dest_x, terrain)

                # Restore tracking dicts at new position
                if snap['slag']:
                    game.slag_wall_tiles[(dest_y, dest_x)] = snap['slag']
                if snap['topiary_terrain']:
                    game.topiary_terrain[(dest_y, dest_x)] = snap['topiary_terrain']

                # Move topiary-unit with its terrain
                if snap['topiary_unit']:
                    tu_data = snap['topiary_unit']
                    topiary_u = tu_data['unit']
                    old_uy, old_ux = topiary_u.y, topiary_u.x
                    topiary_u.y = dest_y
                    topiary_u.x = dest_x
                    game._update_unit_grid(topiary_u, old_uy, old_ux)
                    game.topiary_units[(dest_y, dest_x)] = tu_data

                src_y, src_x = snap['pos']
                rotated_tiles.append({
                    'from': (src_y, src_x),
                    'to': (dest_y, dest_x),
                })

                # Check for non-topiary unit at destination needing displacement
                dest_unit = game.get_unit_at(dest_y, dest_x)
                if dest_unit and dest_unit.is_alive():
                    if not (snap['topiary_unit'] and dest_unit == snap['topiary_unit']['unit']):
                        units_to_displace.append((dest_unit, dest_y, dest_x))

            # Displace units pushed by rotating terrain
            for displaced_unit, at_y, at_x in units_to_displace:
                displaced = False
                for ddy in [-1, 0, 1]:
                    for ddx in [-1, 0, 1]:
                        if ddy == 0 and ddx == 0:
                            continue
                        push_y = at_y + ddy
                        push_x = at_x + ddx
                        if (game.is_valid_position(push_y, push_x) and
                                game.map.is_passable(push_y, push_x) and
                                game.get_unit_at(push_y, push_x) is None):
                            old_dy, old_dx = displaced_unit.y, displaced_unit.x
                            displaced_unit.y = push_y
                            displaced_unit.x = push_x
                            game._update_unit_grid(displaced_unit, old_dy, old_dx)
                            message_log.add_message(
                                f"{displaced_unit.get_display_name()} is displaced by shifting terrain",
                                MessageType.WARNING,
                                player=displaced_unit.player
                            )
                            displaced = True
                            break
                    if displaced:
                        break

            if rotated_tiles:
                message_log.add_message(
                    f"The shockwave whirls surrounding terrain counter-clockwise",
                    MessageType.ABILITY,
                    player=user.player
                )

                # Text mode whirl animation
                if ui and hasattr(ui, 'renderer'):
                    from boneglaive.utils.animation_helpers import sleep_with_animation_speed
                    for tile_info in rotated_tiles:
                        ry, rx = tile_info['to']
                        for frame in ['~', '>', '=']:
                            ui.renderer.draw_damage_text(ry, rx * 2, frame, 2)
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.03)

        # Store execution data for graphical animation to read
        user.last_dissonance_data = {
            'target_pos': (ty, tx),
            'was_topiary': topiary_unit is not None,
            'is_upgraded': is_upgraded,
            'rotated_tiles': rotated_tiles,
        }

        logger.info(f"DISSONANCE EXECUTED: {user.get_display_name()} shattered {shattered_name} "
                     f"at ({ty},{tx}), {total_hits} shrapnel hits for {shrapnel_damage} each"
                     f"{f', {len(rotated_tiles)} tiles rotated' if rotated_tiles else ''}")
