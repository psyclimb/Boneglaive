#!/usr/bin/env python3
"""
Pathfinding Engine for Smart AI.
Finds optimal paths that avoid threats and leverage terrain.
"""

from typing import TYPE_CHECKING, List, Tuple, Set, Optional, Dict
from boneglaive.utils.debug import logger
import heapq

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.ai.battlefield_analyzer import BattlefieldAnalysis


class PathNode:
    """Node in the pathfinding graph."""

    def __init__(self, position: Tuple[int, int], g_cost: float, h_cost: float, parent: Optional['PathNode'] = None):
        self.position = position
        self.g_cost = g_cost  # Cost from start
        self.h_cost = h_cost  # Heuristic cost to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class PathfindingEngine:
    """
    Finds optimal paths considering threats and terrain.
    Uses A* pathfinding with threat-aware cost functions.
    """

    def __init__(self, game: 'Game', ai_player: int):
        """
        Initialize the pathfinding engine.

        Args:
            game: The game instance
            ai_player: The AI's player number
        """
        self.game = game
        self.ai_player = ai_player

    def find_path(self, unit: 'Unit', goal: Tuple[int, int],
                  analysis: 'BattlefieldAnalysis',
                  avoid_threats: bool = True) -> Optional[List[Tuple[int, int]]]:
        """
        Find optimal path from unit's position to goal.

        Args:
            unit: The unit moving
            goal: Goal position (y, x)
            analysis: Battlefield analysis
            avoid_threats: Whether to avoid threatened positions

        Returns:
            List of positions forming path, or None if no path exists
        """
        start = (unit.y, unit.x)

        # A* pathfinding
        open_set = []
        closed_set: Set[Tuple[int, int]] = set()

        start_node = PathNode(start, 0, self._heuristic(start, goal))
        heapq.heappush(open_set, start_node)

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        while open_set:
            current = heapq.heappop(open_set)

            if current.position == goal:
                # Reconstruct path
                return self._reconstruct_path(came_from, current.position, start)

            if current.position in closed_set:
                continue

            closed_set.add(current.position)

            # Check neighbors
            for neighbor_pos in self._get_neighbors(current.position):
                if neighbor_pos in closed_set:
                    continue

                # Calculate cost to move to neighbor
                move_cost = self._calculate_move_cost(unit, neighbor_pos, analysis, avoid_threats)

                # If cost is infinite (blocked), skip
                if move_cost == float('inf'):
                    continue

                g_cost = current.g_cost + move_cost
                h_cost = self._heuristic(neighbor_pos, goal)

                neighbor_node = PathNode(neighbor_pos, g_cost, h_cost, current)
                heapq.heappush(open_set, neighbor_node)
                came_from[neighbor_pos] = current.position

        # No path found
        return None

    def _heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """
        Heuristic function for A* (chess distance).

        Args:
            pos1: First position
            pos2: Second position

        Returns:
            Heuristic cost
        """
        return float(self.game.chess_distance(pos1[0], pos1[1], pos2[0], pos2[1]))

    def _get_neighbors(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get neighboring positions (8 directions for chess distance).

        Args:
            position: Current position

        Returns:
            List of neighbor positions
        """
        y, x = position
        neighbors = []

        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue

                ny, nx = y + dy, x + dx

                # Check bounds
                if 0 <= ny < self.game.map.height and 0 <= nx < self.game.map.width:
                    neighbors.append((ny, nx))

        return neighbors

    def _calculate_move_cost(self, unit: 'Unit', position: Tuple[int, int],
                            analysis: 'BattlefieldAnalysis', avoid_threats: bool) -> float:
        """
        Calculate cost of moving to a position.

        Args:
            unit: Unit moving
            position: Position to evaluate
            analysis: Battlefield analysis
            avoid_threats: Whether to penalize threatened positions

        Returns:
            Movement cost (inf if impassable)
        """
        y, x = position

        # Check if position is passable
        if not self.game.map.is_passable(y, x):
            return float('inf')

        # Check if occupied by another unit
        occupant = self.game.get_unit_at(y, x)
        if occupant is not None:
            return float('inf')

        # Base cost
        cost = 1.0

        # Threat cost
        if avoid_threats and position in analysis.threat_map:
            threat = analysis.threat_map[position]

            # High penalty for deadly threats
            if threat.threat_level >= unit.hp:
                cost += 100.0  # Almost prohibitive
            else:
                # Proportional penalty
                threat_ratio = threat.threat_level / unit.hp
                cost += threat_ratio * 10.0

        return cost

    def _reconstruct_path(self, came_from: Dict[Tuple[int, int], Tuple[int, int]],
                         current: Tuple[int, int], start: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Reconstruct path from came_from dictionary.

        Args:
            came_from: Dictionary mapping position -> previous position
            current: Goal position
            start: Start position

        Returns:
            List of positions forming path
        """
        path = [current]

        while current in came_from:
            current = came_from[current]
            path.append(current)

            if current == start:
                break

        path.reverse()
        return path

    def find_best_approach_position(self, unit: 'Unit', target: 'Unit',
                                   analysis: 'BattlefieldAnalysis',
                                   move_range: int) -> Optional[Tuple[int, int]]:
        """
        Find best position within move_range to approach a target.

        Args:
            unit: Unit moving
            target: Target to approach
            analysis: Battlefield analysis
            move_range: Maximum movement range

        Returns:
            Best position to move to, or None if no good position
        """
        best_pos = None
        best_score = float('-inf')

        # Check all reachable positions
        for y in range(self.game.map.height):
            for x in range(self.game.map.width):
                pos = (y, x)

                # Skip current position
                if pos == (unit.y, unit.x):
                    continue

                # Check if reachable
                distance = self.game.chess_distance(unit.y, unit.x, y, x)
                if distance > move_range:
                    continue

                # Check if passable and unoccupied
                if not self.game.map.is_passable(y, x):
                    continue
                if self.game.get_unit_at(y, x) is not None:
                    continue

                # Score this position
                score = self._score_approach_position(pos, target, unit, analysis)

                if score > best_score:
                    best_score = score
                    best_pos = pos

        return best_pos

    def _score_approach_position(self, position: Tuple[int, int], target: 'Unit',
                                unit: 'Unit', analysis: 'BattlefieldAnalysis') -> float:
        """
        Score a position for approaching a target.

        Args:
            position: Position to evaluate
            target: Target unit
            unit: Moving unit
            analysis: Battlefield analysis

        Returns:
            Position score
        """
        score = 0.0

        # Closer to target is better
        distance_to_target = self.game.chess_distance(position[0], position[1], target.y, target.x)
        score += max(20 - distance_to_target, 0)

        # Safety matters
        if position in analysis.threat_map:
            threat = analysis.threat_map[position]
            if threat.threat_level >= unit.hp:
                score -= 50  # Very bad
            else:
                threat_ratio = threat.threat_level / unit.hp
                score -= threat_ratio * 30

        # Bonus for positions that allow attacking
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        if distance_to_target <= attack_range:
            score += 15  # Can attack from here

        return score

    def find_retreat_position(self, unit: 'Unit', analysis: 'BattlefieldAnalysis',
                            move_range: int) -> Optional[Tuple[int, int]]:
        """
        Find safest position to retreat to.

        Args:
            unit: Unit retreating
            analysis: Battlefield analysis
            move_range: Maximum movement range

        Returns:
            Best retreat position, or None if nowhere is safe
        """
        best_pos = None
        best_score = float('-inf')

        for y in range(self.game.map.height):
            for x in range(self.game.map.width):
                pos = (y, x)

                # Skip current position
                if pos == (unit.y, unit.x):
                    continue

                # Check if reachable
                distance = self.game.chess_distance(unit.y, unit.x, y, x)
                if distance > move_range:
                    continue

                # Check if passable and unoccupied
                if not self.game.map.is_passable(y, x):
                    continue
                if self.game.get_unit_at(y, x) is not None:
                    continue

                # Score safety
                score = self._score_retreat_position(pos, unit, analysis)

                if score > best_score:
                    best_score = score
                    best_pos = pos

        return best_pos

    def _score_retreat_position(self, position: Tuple[int, int],
                               unit: 'Unit', analysis: 'BattlefieldAnalysis') -> float:
        """
        Score a retreat position (safety is paramount).

        Args:
            position: Position to evaluate
            unit: Retreating unit
            analysis: Battlefield analysis

        Returns:
            Safety score
        """
        score = 0.0

        # Huge bonus for safe positions
        if position not in analysis.threat_map:
            score += 50
        else:
            threat = analysis.threat_map[position]
            if threat.threat_level >= unit.hp:
                score -= 100  # Still deadly
            else:
                # Less threat is better
                threat_ratio = threat.threat_level / unit.hp
                score += (1.0 - threat_ratio) * 40

        # Bonus for being near allies
        for ally in analysis.ai_units:
            if ally == unit:
                continue
            distance = self.game.chess_distance(position[0], position[1], ally.y, ally.x)
            if distance <= 3:
                score += 10

        # Bonus for distance from enemies
        if analysis.enemy_units:
            min_enemy_distance = min(self.game.chess_distance(position[0], position[1], e.y, e.x)
                                    for e in analysis.enemy_units)
            score += min_enemy_distance * 2

        return score
