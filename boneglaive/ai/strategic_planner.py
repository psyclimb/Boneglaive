#!/usr/bin/env python3
"""
Strategic Planner for Smart AI.
Determines high-level strategy and team objectives.
"""

from enum import Enum
from typing import TYPE_CHECKING, List, Tuple
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.ai.battlefield_analyzer import BattlefieldAnalysis


class Strategy(Enum):
    """Available strategic approaches."""
    AGGRESSIVE_PUSH = "aggressive_push"      # Push hard, maximize damage
    DEFENSIVE_HOLD = "defensive_hold"        # Protect vulnerable units, hold position
    TRADE_EFFICIENTLY = "trade_efficiently"  # Optimize damage trades
    SECURE_POSITION = "secure_position"      # Improve positioning before attacking
    DESPERATE_RUSH = "desperate_rush"        # All-in attack (when losing badly)


class TeamObjective:
    """A team-wide objective for the turn."""

    def __init__(self, objective_type: str, priority: float, data: dict = None):
        self.type = objective_type
        self.priority = priority
        self.data = data or {}


class StrategicPlan:
    """Container for strategic decisions."""

    def __init__(self):
        self.strategy: Strategy = Strategy.TRADE_EFFICIENTLY
        self.objectives: List[TeamObjective] = []
        self.focus_targets: List['Unit'] = []  # Highest priority enemy targets
        self.defend_units: List['Unit'] = []   # Units that need protection


class StrategicPlanner:
    """
    Determines high-level strategy based on game state.
    Provides objectives and priorities for tactical execution.
    """

    def __init__(self, game: 'Game', ai_player: int):
        """
        Initialize the strategic planner.

        Args:
            game: The game instance
            ai_player: The AI's player number
        """
        self.game = game
        self.ai_player = ai_player

    def plan(self, analysis: 'BattlefieldAnalysis') -> StrategicPlan:
        """
        Create a strategic plan based on battlefield analysis.

        Args:
            analysis: Current battlefield analysis

        Returns:
            Strategic plan for this turn
        """
        plan = StrategicPlan()

        # Choose overall strategy
        plan.strategy = self._choose_strategy(analysis)
        logger.info(f"Strategic plan: {plan.strategy.value}")

        # Set objectives based on strategy
        self._set_objectives(plan, analysis)

        # Identify focus targets
        self._set_focus_targets(plan, analysis)

        # Identify units to defend
        self._set_defend_units(plan, analysis)

        return plan

    def _choose_strategy(self, analysis: 'BattlefieldAnalysis') -> Strategy:
        """
        Choose the best strategy based on current situation.

        Args:
            analysis: Battlefield analysis

        Returns:
            Chosen strategy
        """
        # Evaluate situation
        gp_diff = analysis.gp_difference
        hp_ratio = analysis.ai_avg_hp_percent / analysis.enemy_avg_hp_percent if analysis.enemy_avg_hp_percent > 0 else 1.0
        unit_count_ratio = len(analysis.ai_units) / len(analysis.enemy_units) if analysis.enemy_units else 1.0

        logger.info(f"  Strategy Decision Factors:")
        logger.info(f"    GP difference: {gp_diff:+d}")
        logger.info(f"    HP ratio: {hp_ratio:.2f}")
        logger.info(f"    Unit count ratio: {unit_count_ratio:.2f}")
        logger.info(f"    Vulnerable allies: {len(analysis.vulnerable_allies)}")
        logger.info(f"    Center control: {analysis.ai_center_control:.1%}")

        # Desperate situation: Losing badly on GP and units/HP
        if gp_diff <= -2 and (hp_ratio < 0.6 or unit_count_ratio < 0.7):
            logger.info("  → DESPERATE SITUATION: Going all-in!")
            return Strategy.DESPERATE_RUSH

        # Winning situation: Ahead on GP or resources
        if gp_diff >= 2 or (hp_ratio > 1.3 and unit_count_ratio >= 1.0):
            logger.info("  → WINNING POSITION: Aggressive push!")
            return Strategy.AGGRESSIVE_PUSH

        # Vulnerable situation: Have units in danger
        if len(analysis.vulnerable_allies) >= 2:
            logger.info("  → UNITS IN DANGER: Defensive hold")
            return Strategy.DEFENSIVE_HOLD

        # Poor positioning: Not controlling center
        if analysis.ai_center_control < 0.35:
            logger.info("  → POOR POSITIONING: Securing position")
            return Strategy.SECURE_POSITION

        # Default: Trade efficiently
        logger.info("  → BALANCED: Trading efficiently")
        return Strategy.TRADE_EFFICIENTLY

    def _set_objectives(self, plan: StrategicPlan, analysis: 'BattlefieldAnalysis') -> None:
        """
        Set team objectives based on strategy.

        Args:
            plan: Strategic plan to populate
            analysis: Battlefield analysis
        """
        if plan.strategy == Strategy.AGGRESSIVE_PUSH:
            plan.objectives.append(TeamObjective("maximize_damage", priority=1.0))
            plan.objectives.append(TeamObjective("pressure_enemies", priority=0.8))
            plan.objectives.append(TeamObjective("secure_kills", priority=0.9))

        elif plan.strategy == Strategy.DEFENSIVE_HOLD:
            plan.objectives.append(TeamObjective("protect_vulnerable", priority=1.0))
            plan.objectives.append(TeamObjective("maintain_formation", priority=0.7))
            plan.objectives.append(TeamObjective("safe_attacks", priority=0.5))

        elif plan.strategy == Strategy.TRADE_EFFICIENTLY:
            plan.objectives.append(TeamObjective("favorable_trades", priority=1.0))
            plan.objectives.append(TeamObjective("secure_kills", priority=0.7))
            plan.objectives.append(TeamObjective("avoid_danger", priority=0.6))

        elif plan.strategy == Strategy.SECURE_POSITION:
            plan.objectives.append(TeamObjective("improve_positioning", priority=1.0))
            plan.objectives.append(TeamObjective("control_center", priority=0.8))
            plan.objectives.append(TeamObjective("maintain_formation", priority=0.6))

        elif plan.strategy == Strategy.DESPERATE_RUSH:
            plan.objectives.append(TeamObjective("maximize_damage", priority=1.0))
            plan.objectives.append(TeamObjective("secure_kills", priority=1.0))
            plan.objectives.append(TeamObjective("ignore_safety", priority=0.0))

    def _set_focus_targets(self, plan: StrategicPlan, analysis: 'BattlefieldAnalysis') -> None:
        """
        Identify which enemies to focus on.

        Args:
            plan: Strategic plan to populate
            analysis: Battlefield analysis
        """
        # Get top priority targets based on strategy
        if plan.strategy == Strategy.AGGRESSIVE_PUSH or plan.strategy == Strategy.DESPERATE_RUSH:
            # Focus on closest or most isolated targets
            num_targets = min(3, len(analysis.priority_targets))
            plan.focus_targets = [target for target, _ in analysis.priority_targets[:num_targets]]

        elif plan.strategy == Strategy.DEFENSIVE_HOLD:
            # Focus on threats to vulnerable allies
            threats_to_vulnerable = set()
            for ally, _ in analysis.vulnerable_allies[:2]:
                pos = (ally.y, ally.x)
                if pos in analysis.threat_map:
                    threat_zone = analysis.threat_map[pos]
                    threats_to_vulnerable.update(threat_zone.threatening_units)

            plan.focus_targets = list(threats_to_vulnerable)

        else:  # TRADE_EFFICIENTLY or SECURE_POSITION
            # Focus on top 2 priority targets
            num_targets = min(2, len(analysis.priority_targets))
            plan.focus_targets = [target for target, _ in analysis.priority_targets[:num_targets]]

        logger.debug(f"Focus targets: {[t.get_display_name() for t in plan.focus_targets]}")

    def _set_defend_units(self, plan: StrategicPlan, analysis: 'BattlefieldAnalysis') -> None:
        """
        Identify which AI units need protection.

        Args:
            plan: Strategic plan to populate
            analysis: Battlefield analysis
        """
        if plan.strategy == Strategy.DEFENSIVE_HOLD:
            # Protect all vulnerable units
            plan.defend_units = [unit for unit, _ in analysis.vulnerable_allies]

        elif plan.strategy == Strategy.TRADE_EFFICIENTLY or plan.strategy == Strategy.SECURE_POSITION:
            # Protect most vulnerable unit
            if analysis.vulnerable_allies:
                plan.defend_units = [analysis.vulnerable_allies[0][0]]

        # Don't protect anyone in desperate rush
        # Aggressive push also doesn't prioritize defense

        if plan.defend_units:
            logger.debug(f"Defend units: {[u.get_display_name() for u in plan.defend_units]}")

    def should_be_aggressive(self, plan: StrategicPlan) -> bool:
        """
        Check if current strategy calls for aggressive play.

        Args:
            plan: Current strategic plan

        Returns:
            True if strategy is aggressive
        """
        return plan.strategy in [Strategy.AGGRESSIVE_PUSH, Strategy.DESPERATE_RUSH]

    def should_prioritize_safety(self, plan: StrategicPlan) -> bool:
        """
        Check if current strategy prioritizes safety.

        Args:
            plan: Current strategic plan

        Returns:
            True if strategy prioritizes safety
        """
        return plan.strategy in [Strategy.DEFENSIVE_HOLD, Strategy.TRADE_EFFICIENTLY]

    def get_objective_priority(self, plan: StrategicPlan, objective_type: str) -> float:
        """
        Get priority value for a specific objective.

        Args:
            plan: Current strategic plan
            objective_type: Type of objective to query

        Returns:
            Priority value (0.0 to 1.0)
        """
        for objective in plan.objectives:
            if objective.type == objective_type:
                return objective.priority
        return 0.0
