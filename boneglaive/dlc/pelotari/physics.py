#!/usr/bin/env python3
"""
Ball physics system for PELOTARI.

Handles ricochet trajectories, angle of incidence, phase mode, and spread shot patterns.
"""

import math
from typing import List, Tuple, Optional, TYPE_CHECKING

from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.engine import Game


def calculate_spread_shot_trajectories(start_pos: Tuple[int, int], cone_angle: int,
                                       ball_count: int, ricochet_mode: bool,
                                       game: 'Game') -> List[List[Tuple[int, int]]]:
    """
    Calculate trajectories for spread shot (Riposte passive).

    Args:
        start_pos: Starting position (y, x)
        cone_angle: Cone angle in degrees (120)
        ball_count: Number of balls (6)
        ricochet_mode: True for ricochet, False for phase
        game: Game instance

    Returns:
        List of trajectories, each trajectory is list of (y, x) positions
    """
    trajectories = []

    # Calculate angle step between balls
    angle_step = cone_angle / (ball_count - 1) if ball_count > 1 else 0
    start_angle = -cone_angle / 2  # Start from left side of cone

    for i in range(ball_count):
        angle = start_angle + (i * angle_step)
        # Convert angle to direction vector
        direction = angle_to_direction(angle)

        # Calculate trajectory for this ball
        trajectory = calculate_linear_trajectory(
            start_pos=start_pos,
            direction=direction,
            ricochet_mode=ricochet_mode,
            max_range=999,  # Unlimited range
            game=game
        )
        trajectories.append(trajectory)

    logger.debug(f"Spread shot: {ball_count} trajectories calculated")
    return trajectories


def calculate_buff_ball_trajectory(start_pos: Tuple[int, int], ricochet_mode: bool,
                                   game: 'Game') -> List[Tuple[int, int]]:
    """
    Calculate trajectory for buff ball from Poach skill.

    Args:
        start_pos: Starting position (y, x)
        ricochet_mode: True for ricochet, False for phase
        game: Game instance

    Returns:
        List of (y, x) positions ball travels through
    """
    # Buff ball travels in a default outward direction
    # TODO: Determine smart direction based on ally positions
    direction = (0, 1)  # Default: travel right

    trajectory = calculate_linear_trajectory(
        start_pos=start_pos,
        direction=direction,
        ricochet_mode=ricochet_mode,
        max_range=999,  # Travel until hitting ally or boundary
        game=game
    )

    return trajectory


def calculate_reflection_trajectory(start_pos: Tuple[int, int], target_pos: Tuple[int, int],
                                    ricochet_mode: bool, game: 'Game') -> List[Tuple[int, int]]:
    """
    Calculate trajectory for Backhand reflection.

    Args:
        start_pos: PELOTARI position (y, x)
        target_pos: Attacker position (y, x)
        ricochet_mode: True for ricochet, False for phase
        game: Game instance

    Returns:
        List of (y, x) positions ball travels through
    """
    # Calculate direction from PELOTARI to attacker
    direction = (
        target_pos[0] - start_pos[0],
        target_pos[1] - start_pos[1]
    )

    # Normalize direction
    direction = normalize_direction(direction)

    trajectory = calculate_linear_trajectory(
        start_pos=start_pos,
        direction=direction,
        ricochet_mode=ricochet_mode,
        max_range=999,
        game=game
    )

    return trajectory


def calculate_cannonball_trajectory(start_pos: Tuple[int, int], target_pos: Tuple[int, int],
                                    ricochet_mode: bool, game: 'Game') -> List[Tuple[int, int]]:
    """
    Calculate trajectory for Cannonball skill.

    Args:
        start_pos: PELOTARI position (y, x)
        target_pos: Target position (y, x)
        ricochet_mode: True for ricochet, False for phase
        game: Game instance

    Returns:
        List of (y, x) positions ball travels through
    """
    # Calculate direction
    direction = (
        target_pos[0] - start_pos[0],
        target_pos[1] - start_pos[1]
    )

    direction = normalize_direction(direction)

    trajectory = calculate_linear_trajectory(
        start_pos=start_pos,
        direction=direction,
        ricochet_mode=ricochet_mode,
        max_range=game.chess_distance(start_pos[0], start_pos[1], target_pos[0], target_pos[1]) + 5,
        game=game,
        is_cannonball=True  # Special flag for furniture interaction
    )

    return trajectory


def calculate_linear_trajectory(start_pos: Tuple[int, int], direction: Tuple[int, int],
                                ricochet_mode: bool, max_range: int, game: 'Game',
                                is_cannonball: bool = False) -> List[Tuple[int, int]]:
    """
    Calculate linear trajectory with optional ricochet.

    Args:
        start_pos: Starting position (y, x)
        direction: Direction vector (dy, dx)
        ricochet_mode: True for ricochet, False for phase
        max_range: Maximum range in tiles
        game: Game instance
        is_cannonball: Special handling for Cannonball skill

    Returns:
        List of (y, x) positions
    """
    trajectory = []
    current_pos = start_pos
    current_direction = direction
    bounced = False  # Track if ball has bounced

    for step in range(max_range):
        # Move one step
        next_y = current_pos[0] + current_direction[0]
        next_x = current_pos[1] + current_direction[1]
        next_pos = (next_y, next_x)

        logger.debug(f"Step {step}: at {current_pos}, dir {current_direction}, next {next_pos}, bounced={bounced}")

        # Check bounds
        if not game.is_valid_position(next_y, next_x):
            # Hit map edge
            if not ricochet_mode:
                # Phase mode: bounce off edges
                current_direction = calculate_bounce_off_edge(
                    current_pos, current_direction, game
                )
                continue
            else:
                # Ricochet mode: stop at edge
                break

        # Check terrain
        if not game.map.is_passable(next_y, next_x):
            if ricochet_mode and not bounced:
                # Ricochet mode: bounce once
                new_direction = calculate_bounce(
                    current_pos=current_pos,
                    incoming_direction=current_direction,
                    game=game
                )
                if new_direction:
                    current_direction = new_direction
                    bounced = True
                    logger.debug(f"Ball at {current_pos} hit wall at {next_pos}, incoming: {current_direction}, new: {new_direction}")
                    continue
                else:
                    # Can't bounce, stop
                    break
            elif not ricochet_mode:
                # Phase mode: pass through terrain
                trajectory.append(next_pos)
                current_pos = next_pos
                continue
            else:
                # Already bounced once, stop
                break

        # Add position to trajectory
        trajectory.append(next_pos)
        current_pos = next_pos

    logger.debug(f"Trajectory complete: {len(trajectory)} positions, bounced={bounced}")
    return trajectory


def calculate_bounce(current_pos: Tuple[int, int], incoming_direction: Tuple[int, int],
                     game: 'Game') -> Optional[Tuple[int, int]]:
    """
    Calculate bounce using edge-ricochet logic - checks which wall faces are exposed.

    Args:
        current_pos: Wall tile position that ball hit
        incoming_direction: Direction ball was traveling (dy, dx)
        game: Game instance

    Returns:
        New direction (dy, dx)
    """
    dy, dx = incoming_direction
    reflection = [dy, dx]

    # Check if current_pos is a wall tile
    is_wall = not game.map.is_passable(current_pos[0], current_pos[1])

    if is_wall:
        # Check which edges of the wall face open space
        at_left_edge = current_pos[1] == 0 or \
                      (current_pos[1] > 0 and game.map.is_passable(current_pos[0], current_pos[1] - 1))
        at_right_edge = current_pos[1] == game.map.width - 1 or \
                       (current_pos[1] < game.map.width - 1 and game.map.is_passable(current_pos[0], current_pos[1] + 1))
        at_top_edge = current_pos[0] == 0 or \
                     (current_pos[0] > 0 and game.map.is_passable(current_pos[0] - 1, current_pos[1]))
        at_bottom_edge = current_pos[0] == game.map.height - 1 or \
                        (current_pos[0] < game.map.height - 1 and game.map.is_passable(current_pos[0] + 1, current_pos[1]))

        # Flip based on which edge faces open space (same as map edge logic)
        if at_left_edge or at_right_edge:
            reflection[1] = -reflection[1]
        if at_top_edge or at_bottom_edge:
            reflection[0] = -reflection[0]
    else:
        # Not a wall (shouldn't happen, but handle it) - bounce straight back
        reflection[0] = -reflection[0]
        reflection[1] = -reflection[1]

    return tuple(reflection)


def calculate_surface_normal(impact_pos: Tuple[int, int], game: 'Game') -> Optional[Tuple[int, int]]:
    """
    DEPRECATED: No longer used. Kept for backwards compatibility.

    The new bounce system uses simple directional rules instead of surface normals.

    Args:
        impact_pos: Position of impact
        game: Game instance

    Returns:
        None (deprecated)
    """
    return None


def calculate_bounce_off_edge(current_pos: Tuple[int, int], direction: Tuple[int, int],
                              game: 'Game') -> Tuple[int, int]:
    """
    Calculate bounce off map edge (phase mode only).

    Args:
        current_pos: Current position
        direction: Current direction
        game: Game instance

    Returns:
        New direction after bouncing
    """
    next_y = current_pos[0] + direction[0]
    next_x = current_pos[1] + direction[1]

    new_dir = list(direction)

    # Check which edge was hit
    if next_y < 0 or next_y >= game.map.height:
        # Hit top or bottom edge, flip vertical
        new_dir[0] = -new_dir[0]
    if next_x < 0 or next_x >= game.map.width:
        # Hit left or right edge, flip horizontal
        new_dir[1] = -new_dir[1]

    return tuple(new_dir)


def angle_to_direction(angle_degrees: float) -> Tuple[int, int]:
    """
    Convert angle to chess direction vector.

    Args:
        angle_degrees: Angle in degrees (0 = right, 90 = up)

    Returns:
        Direction tuple (dy, dx) - quantized to 8 cardinal/diagonal directions
    """
    # Convert to radians
    angle_rad = math.radians(angle_degrees)

    # Calculate continuous direction
    dx = math.cos(angle_rad)
    dy = -math.sin(angle_rad)  # Negative because y increases downward

    # Quantize to 8 directions
    # Determine which of 8 directions is closest
    directions_8 = [
        (0, 1),   # E
        (-1, 1),  # NE
        (-1, 0),  # N
        (-1, -1), # NW
        (0, -1),  # W
        (1, -1),  # SW
        (1, 0),   # S
        (1, 1)    # SE
    ]

    # Find closest direction
    best_dir = directions_8[0]
    best_dot = dx * best_dir[1] + dy * best_dir[0]

    for direction in directions_8[1:]:
        dot = dx * direction[1] + dy * direction[0]
        if dot > best_dot:
            best_dot = dot
            best_dir = direction

    return best_dir


def normalize_direction(direction: Tuple[int, int]) -> Tuple[int, int]:
    """
    Normalize direction to unit vector (quantized to 8 chess directions).

    Args:
        direction: Direction tuple (dy, dx)

    Returns:
        Normalized direction
    """
    dy, dx = direction

    if dy == 0 and dx == 0:
        return (0, 1)  # Default direction

    # Quantize to -1, 0, 1
    norm_dy = 0 if dy == 0 else (1 if dy > 0 else -1)
    norm_dx = 0 if dx == 0 else (1 if dx > 0 else -1)

    return (norm_dy, norm_dx)
