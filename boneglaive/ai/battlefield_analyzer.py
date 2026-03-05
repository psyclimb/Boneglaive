#!/usr/bin/env python3
"""
Battlefield Analyzer for Smart AI.
Analyzes game state to provide tactical intelligence.
"""

from typing import Dict, List, Set, Tuple, Optional, TYPE_CHECKING
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit


class ThreatZone:
    """Represents a position's threat level from enemy units."""

    def __init__(self, position: Tuple[int, int]):
        self.position = position
        self.threatening_units: List['Unit'] = []  # Units that can attack this position
        self.threat_level: int = 0  # Total potential damage

    def add_threat(self, unit: 'Unit', potential_damage: int) -> None:
        """Add a threatening unit and its potential damage."""
        self.threatening_units.append(unit)
        self.threat_level += potential_damage


class BattlefieldAnalysis:
    """Container for battlefield analysis results."""

    def __init__(self):
        # Threat mapping
        self.threat_map: Dict[Tuple[int, int], ThreatZone] = {}

        # Unit tracking
        self.ai_units: List['Unit'] = []
        self.enemy_units: List['Unit'] = []

        # Strategic metrics
        self.ai_total_hp: int = 0
        self.enemy_total_hp: int = 0
        self.ai_avg_hp_percent: float = 0.0
        self.enemy_avg_hp_percent: float = 0.0

        # GP tracking
        self.ai_gp: int = 0
        self.enemy_gp: int = 0
        self.gp_difference: int = 0  # positive = AI winning

        # Positional advantage
        self.ai_center_control: float = 0.0  # 0-1 score for map control
        self.enemy_center_control: float = 0.0

        # Priority targets (sorted by value)
        self.priority_targets: List[Tuple['Unit', float]] = []  # (unit, score)

        # Vulnerable allies (units in danger)
        self.vulnerable_allies: List[Tuple['Unit', float]] = []  # (unit, danger_score)


class BattlefieldAnalyzer:
    """
    Analyzes the battlefield state to provide tactical intelligence.
    Generates threat maps, identifies priority targets, evaluates positioning.
    """

    def __init__(self, game: 'Game', ai_player: int):
        """
        Initialize the analyzer.

        Args:
            game: The game instance
            ai_player: The AI's player number (1 or 2)
        """
        self.game = game
        self.ai_player = ai_player
        self.enemy_player = 3 - ai_player  # 1->2, 2->1

    def analyze(self) -> BattlefieldAnalysis:
        """
        Perform complete battlefield analysis.

        Returns:
            BattlefieldAnalysis object with all tactical data
        """
        analysis = BattlefieldAnalysis()

        # Categorize units
        self._categorize_units(analysis)

        # Calculate health metrics
        self._calculate_health_metrics(analysis)

        # Get GP status
        self._calculate_gp_status(analysis)

        # Build threat map
        self._build_threat_map(analysis)

        # Evaluate map control
        self._evaluate_map_control(analysis)

        # Identify priority targets
        self._identify_priority_targets(analysis)

        # Find vulnerable allies
        self._identify_vulnerable_allies(analysis)

        logger.debug(f"Battlefield analysis complete: {len(analysis.ai_units)} AI units, "
                    f"{len(analysis.enemy_units)} enemy units, GP: {analysis.ai_gp}-{analysis.enemy_gp}")

        return analysis

    def _categorize_units(self, analysis: BattlefieldAnalysis) -> None:
        """Separate AI and enemy units."""
        for unit in self.game.units:
            if not unit.is_alive():
                continue

            if unit.player == self.ai_player:
                analysis.ai_units.append(unit)
            else:
                # Skip untargetable enemies (e.g., INTERFERER under Karrier Rave)
                if hasattr(unit, 'is_untargetable') and unit.is_untargetable():
                    continue
                analysis.enemy_units.append(unit)

    def _calculate_health_metrics(self, analysis: BattlefieldAnalysis) -> None:
        """Calculate HP totals and percentages."""
        if analysis.ai_units:
            analysis.ai_total_hp = sum(u.hp for u in analysis.ai_units)
            ai_max_hp = sum(u.max_hp for u in analysis.ai_units)
            analysis.ai_avg_hp_percent = analysis.ai_total_hp / ai_max_hp if ai_max_hp > 0 else 0

        if analysis.enemy_units:
            analysis.enemy_total_hp = sum(u.hp for u in analysis.enemy_units)
            enemy_max_hp = sum(u.max_hp for u in analysis.enemy_units)
            analysis.enemy_avg_hp_percent = analysis.enemy_total_hp / enemy_max_hp if enemy_max_hp > 0 else 0

    def _calculate_gp_status(self, analysis: BattlefieldAnalysis) -> None:
        """Get current GP scores."""
        if self.ai_player == 1:
            analysis.ai_gp = self.game.player1_gp
            analysis.enemy_gp = self.game.player2_gp
        else:
            analysis.ai_gp = self.game.player2_gp
            analysis.enemy_gp = self.game.player1_gp

        analysis.gp_difference = analysis.ai_gp - analysis.enemy_gp

    def _build_threat_map(self, analysis: BattlefieldAnalysis) -> None:
        """
        Build a map of threat zones showing where enemies can attack.
        """
        # For each enemy unit, mark all positions they can attack
        for enemy in analysis.enemy_units:
            stats = enemy.get_effective_stats()
            attack_range = stats['attack_range']
            potential_damage = stats['attack']

            # Check all positions within attack range
            for y in range(self.game.map.height):
                for x in range(self.game.map.width):
                    distance = self.game.chess_distance(enemy.y, enemy.x, y, x)

                    if distance <= attack_range and distance > 0:
                        pos = (y, x)
                        if pos not in analysis.threat_map:
                            analysis.threat_map[pos] = ThreatZone(pos)

                        analysis.threat_map[pos].add_threat(enemy, potential_damage)

    def _evaluate_map_control(self, analysis: BattlefieldAnalysis) -> None:
        """
        Evaluate positional control of the map.
        Units closer to center have more control.
        """
        center_y = self.game.map.height // 2
        center_x = self.game.map.width // 2

        ai_control_score = 0
        enemy_control_score = 0

        for unit in analysis.ai_units:
            distance_to_center = self.game.chess_distance(unit.y, unit.x, center_y, center_x)
            # Closer to center = higher score (inverse distance)
            control_value = max(10 - distance_to_center, 0)
            ai_control_score += control_value

        for unit in analysis.enemy_units:
            distance_to_center = self.game.chess_distance(unit.y, unit.x, center_y, center_x)
            control_value = max(10 - distance_to_center, 0)
            enemy_control_score += control_value

        total_control = ai_control_score + enemy_control_score
        if total_control > 0:
            analysis.ai_center_control = ai_control_score / total_control
            analysis.enemy_center_control = enemy_control_score / total_control

    def _identify_priority_targets(self, analysis: BattlefieldAnalysis) -> None:
        """
        Identify and score enemy units as priority targets.
        Higher score = higher priority.
        """
        target_scores = []

        for enemy in analysis.enemy_units:
            score = 0.0

            # Factor 1: Low HP targets (easier kills)
            hp_percent = enemy.hp / enemy.max_hp
            score += (1.0 - hp_percent) * 30  # Up to 30 points for low HP

            # Factor 2: High attack power (dangerous targets)
            stats = enemy.get_effective_stats()
            score += stats['attack'] * 0.5  # Attack damage contributes to priority

            # Factor 3: Proximity to AI units (reachable targets)
            # Only calculate if AI has units alive (prevents min() on empty sequence)
            if analysis.ai_units:
                min_distance = min(self.game.chess_distance(enemy.y, enemy.x, ally.y, ally.x)
                                 for ally in analysis.ai_units)
                proximity_score = max(15 - min_distance, 0)
                score += proximity_score

            # Factor 4: Isolated units (easier to kill without support)
            if len(analysis.enemy_units) > 1:
                avg_distance_to_allies = sum(
                    self.game.chess_distance(enemy.y, enemy.x, other.y, other.x)
                    for other in analysis.enemy_units if other != enemy
                ) / (len(analysis.enemy_units) - 1)

                if avg_distance_to_allies > 4:
                    score += 10  # Bonus for isolated targets

            target_scores.append((enemy, score))

        # Sort by score (highest first)
        analysis.priority_targets = sorted(target_scores, key=lambda x: x[1], reverse=True)

    def _identify_vulnerable_allies(self, analysis: BattlefieldAnalysis) -> None:
        """
        Identify AI units in danger.
        Higher danger score = more vulnerable.
        """
        vulnerable = []

        for ally in analysis.ai_units:
            danger_score = 0.0

            # Check if unit is in threat zone
            pos = (ally.y, ally.x)
            if pos in analysis.threat_map:
                threat = analysis.threat_map[pos]
                # Danger increases with potential damage relative to current HP
                if ally.hp > 0:
                    damage_ratio = threat.threat_level / ally.hp
                    danger_score += damage_ratio * 20

                # More threatening units = more danger
                danger_score += len(threat.threatening_units) * 5

            # Low HP units are more vulnerable
            hp_percent = ally.hp / ally.max_hp
            if hp_percent < 0.3:
                danger_score += 15
            elif hp_percent < 0.5:
                danger_score += 8

            # Isolated units are more vulnerable
            if len(analysis.ai_units) > 1:
                min_distance_to_ally = min(
                    self.game.chess_distance(ally.y, ally.x, other.y, other.x)
                    for other in analysis.ai_units if other != ally
                )
                if min_distance_to_ally > 5:
                    danger_score += 10

            if danger_score > 0:
                vulnerable.append((ally, danger_score))

        # Sort by danger (highest first)
        analysis.vulnerable_allies = sorted(vulnerable, key=lambda x: x[1], reverse=True)

    def get_threat_at_position(self, analysis: BattlefieldAnalysis,
                               y: int, x: int) -> Optional[ThreatZone]:
        """
        Get threat information for a specific position.

        Args:
            analysis: The battlefield analysis
            y, x: Position to check

        Returns:
            ThreatZone if position is threatened, None otherwise
        """
        return analysis.threat_map.get((y, x))

    def is_position_safe(self, analysis: BattlefieldAnalysis,
                        y: int, x: int, unit_hp: int) -> bool:
        """
        Check if a position is safe for a unit with given HP.

        Args:
            analysis: The battlefield analysis
            y, x: Position to check
            unit_hp: HP of the unit considering this position

        Returns:
            True if position is safe (threat level < 50% of HP)
        """
        threat = self.get_threat_at_position(analysis, y, x)
        if not threat:
            return True

        # Position is safe if threat level is less than 50% of unit's HP
        return threat.threat_level < (unit_hp * 0.5)
