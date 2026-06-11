#!/usr/bin/env python3
"""
Smart AI Controller for Boneglaive.
Orchestrates modular AI systems for intelligent gameplay.
"""

from typing import Optional, TYPE_CHECKING
from boneglaive.utils.debug import logger
from boneglaive.ai.battlefield_analyzer import BattlefieldAnalyzer
from boneglaive.ai.strategic_planner import StrategicPlanner
from boneglaive.ai.tactical_evaluator import TacticalEvaluator, Action
from boneglaive.ai.skill_simulator import SkillSimulator
from boneglaive.ai.pathfinding import PathfindingEngine

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.ui.game_ui import GameUI


class SmartAI:
    """
    Intelligent AI controller using modular decision-making systems.
    Modular AI controller with strategic thinking.
    """

    def __init__(self, game: 'Game', ui: Optional['GameUI'] = None):
        """
        Initialize the Smart AI.

        Args:
            game: Reference to the Game instance
            ui: Optional reference to the GameUI instance
        """
        self.game = game
        self.ui = ui
        self.player_number = 2  # AI is always player 2

        # Initialize AI modules
        self.analyzer = BattlefieldAnalyzer(game, self.player_number)
        self.planner = StrategicPlanner(game, self.player_number)
        self.evaluator = TacticalEvaluator(game, self.player_number)
        self.skill_sim = SkillSimulator(game, self.player_number)
        self.pathfinder = PathfindingEngine(game, self.player_number)

        logger.info("Smart AI initialized")

    def process_turn(self) -> bool:
        """
        Process a full AI turn using intelligent decision-making.

        Returns:
            True if turn processed successfully
        """
        try:
            # Analyze the battlefield
            analysis = self.analyzer.analyze()

            # Create strategic plan
            plan = self.planner.plan(analysis)

            # Handle respawns if any
            self._handle_respawns(analysis)

            # Process each unit
            for unit in analysis.ai_units:
                self._process_unit(unit, analysis, plan)

                # Update UI after each unit
                if self.ui:
                    self.ui.draw_board()

            return True

        except Exception as e:
            import traceback
            logger.error(f"Error in Smart AI turn: {e}")
            logger.error(traceback.format_exc())
            return True  # Return True to allow turn to complete

    def _handle_respawns(self, analysis) -> None:
        """
        Handle unit respawns intelligently.

        Args:
            analysis: Battlefield analysis
        """
        ready_dead_units = [du for du in self.game.dead_units
                           if du.player == self.player_number and du.ready_for_respawn]

        if not ready_dead_units:
            return

        for dead_unit in ready_dead_units:
            spawn_location = self._find_respawn_location(dead_unit, analysis)

            if spawn_location:
                success = self.game.queue_respawn(dead_unit, spawn_location)
                if success:
                    logger.info(f"AI queued respawn for {dead_unit.greek_id}")

    def _find_respawn_location(self, dead_unit, analysis) -> Optional[tuple]:
        """
        Find optimal respawn location.

        Args:
            dead_unit: DeadUnit to respawn
            analysis: Battlefield analysis

        Returns:
            Best spawn position (y, x) or None
        """
        valid_positions = []

        # Find all valid spawn positions
        for y in range(self.game.map.height):
            for x in range(self.game.map.width):
                if (self.game.is_valid_position(y, x) and
                    self.game.map.is_passable(y, x) and
                    not self.game.get_unit_at(y, x)):
                    valid_positions.append((y, x))

        if not valid_positions:
            return None

        # Score positions
        best_pos = None
        best_score = float('-inf')

        for pos in valid_positions:
            score = self._score_spawn_position(pos, analysis)
            if score > best_score:
                best_score = score
                best_pos = pos

        return best_pos

    def _score_spawn_position(self, pos: tuple, analysis) -> float:
        """
        Score a spawn position.

        Args:
            pos: Position to score
            analysis: Battlefield analysis

        Returns:
            Position score
        """
        score = 0.0

        # Prefer safe positions
        if pos not in analysis.threat_map:
            score += 30
        else:
            threat = analysis.threat_map[pos]
            score -= threat.threat_level

        # Prefer positions near allies
        if analysis.ai_units:
            min_distance = min(self.game.chess_distance(pos[0], pos[1], ally.y, ally.x)
                             for ally in analysis.ai_units)
            # Sweet spot: 3-5 tiles away
            if 3 <= min_distance <= 5:
                score += 20
            elif min_distance < 3:
                score += 5
            else:
                score -= min_distance

        return score

    def _process_unit(self, unit: 'Unit', analysis, plan) -> None:
        """
        Process actions for a single unit.

        Args:
            unit: Unit to process
            analysis: Battlefield analysis
            plan: Strategic plan
        """
        # Topiary units cannot act
        if getattr(unit, 'is_topiary', False):
            return

        # Reset unit targets
        unit.move_target = None
        unit.attack_target = None
        unit.skill_target = None
        unit.selected_skill = None

        # Evaluate all possible actions
        try:
            actions = self.evaluator.evaluate_unit_actions(unit, analysis, plan)
        except Exception as e:
            logger.error(f"Error evaluating actions for {unit.get_display_name()}: {e}")
            return

        if not actions:
            return

        # Execute best action
        best_action = actions[0]

        try:
            self._execute_action(unit, best_action)
        except Exception as e:
            logger.error(f"Error executing action for {unit.get_display_name()}: {e}")

    def _execute_action(self, unit: 'Unit', action: Action) -> None:
        """
        Execute the chosen action.

        Args:
            unit: Unit performing action
            action: Action to execute
        """
        if action.type == "attack":
            from boneglaive.utils.constants import UnitType
            target = action.target
            unit.attack_target = (target.y, target.x)

            # DERELICTIONIST: activate Severance and set retreat move to maximize damage
            if unit.type == UnitType.DERELICTIONIST:
                unit.can_move_post_skill = True
                unit.used_skill_this_turn = True
                unit.severance_active = True
                unit.severance_duration = 1
                unit.attack_queued_from = (unit.y, unit.x)
                # Use pre-computed retreat position if available, otherwise compute it
                if 'severance_move' in action.data:
                    retreat_pos = action.data['severance_move']
                else:
                    retreat_pos = self.evaluator._derelictionist_best_retreat(unit, target)
                if retreat_pos != (unit.y, unit.x):
                    unit.move_target = retreat_pos

        elif action.type == "move":
            pos = action.target
            unit.move_target = pos

        elif action.type == "skill":
            skill, target = action.target

            # Convert target to position tuple
            if hasattr(target, 'y'):  # It's a unit
                target_pos = (target.y, target.x)
            else:  # It's a position
                target_pos = target

            # IMPORTANT: Call skill.use() to properly queue the skill AND set cooldown
            # Previously this just set unit.selected_skill directly, bypassing cooldown logic
            skill.use(unit, target_pos, self.game)

        elif action.type == "move_attack":
            move_pos, attack_target = action.target
            unit.move_target = move_pos
            unit.attack_target = (attack_target.y, attack_target.x)
