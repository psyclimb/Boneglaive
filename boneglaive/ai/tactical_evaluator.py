#!/usr/bin/env python3
"""
Tactical Evaluator for Smart AI.
Scores individual unit actions to find optimal choices.
"""

from typing import TYPE_CHECKING, List, Tuple, Optional, Dict
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.ai.battlefield_analyzer import BattlefieldAnalysis
    from boneglaive.ai.strategic_planner import StrategicPlan


class Action:
    """Represents a possible action for a unit."""

    def __init__(self, action_type: str, target=None, priority: float = 0.0):
        self.type = action_type  # "move", "attack", "skill", "move_attack"
        self.target = target     # Position tuple or Unit or (skill, target)
        self.priority = priority # Evaluated score
        self.data = {}          # Additional action data


class TacticalEvaluator:
    """
    Evaluates and scores possible actions for individual units.
    Considers strategic objectives when scoring.
    """

    def __init__(self, game: 'Game', ai_player: int):
        """
        Initialize the tactical evaluator.

        Args:
            game: The game instance
            ai_player: The AI's player number
        """
        self.game = game
        self.ai_player = ai_player

    def evaluate_unit_actions(self, unit: 'Unit', analysis: 'BattlefieldAnalysis',
                              plan: 'StrategicPlan') -> List[Action]:
        """
        Evaluate all possible actions for a unit and return them sorted by score.

        Args:
            unit: The unit to evaluate actions for
            analysis: Current battlefield analysis
            plan: Current strategic plan

        Returns:
            List of actions sorted by priority (highest first)
        """
        actions = []

        # Generate and score all possible actions
        logger.debug(f"      Evaluating attacks...")
        attacks = self._evaluate_attacks(unit, analysis, plan)
        logger.debug(f"        Found {len(attacks)} attack actions")
        actions.extend(attacks)

        logger.debug(f"      Evaluating moves...")
        moves = self._evaluate_moves(unit, analysis, plan)
        logger.debug(f"        Found {len(moves)} move actions")
        actions.extend(moves)

        logger.debug(f"      Evaluating skills...")
        try:
            skills = self._evaluate_skills(unit, analysis, plan)
            logger.debug(f"        Found {len(skills)} skill actions")
            actions.extend(skills)
        except Exception as e:
            logger.error(f"        Error evaluating skills: {e}")

        logger.debug(f"      Evaluating move+attack combos...")
        combos = self._evaluate_move_attack_combos(unit, analysis, plan)
        logger.debug(f"        Found {len(combos)} combo actions")
        actions.extend(combos)

        # Sort by priority (highest first)
        actions.sort(key=lambda a: a.priority, reverse=True)

        logger.debug(f"      Total actions evaluated: {len(actions)}")
        if actions:
            logger.debug(f"      Top 3: {[(a.type, round(a.priority, 1)) for a in actions[:3]]}")

        return actions

    def _evaluate_attacks(self, unit: 'Unit', analysis: 'BattlefieldAnalysis',
                         plan: 'StrategicPlan') -> List[Action]:
        """
        Evaluate direct attack actions from current position.

        Args:
            unit: The unit to evaluate
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of attack actions with scores
        """
        actions = []
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']
        damage = stats['attack']

        # Check each enemy for attackability
        for enemy in analysis.enemy_units:
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)

            if distance <= attack_range and distance > 0:
                score = self._score_attack(unit, enemy, analysis, plan, damage)
                action = Action("attack", target=enemy, priority=score)
                action.data['can_kill'] = enemy.hp <= damage
                actions.append(action)

        return actions

    def _score_attack(self, attacker: 'Unit', target: 'Unit',
                     analysis: 'BattlefieldAnalysis', plan: 'StrategicPlan',
                     damage: int) -> float:
        """
        Score an attack action.

        Args:
            attacker: Unit performing attack
            target: Enemy being attacked
            analysis: Battlefield analysis
            plan: Strategic plan
            damage: Expected damage

        Returns:
            Attack score
        """
        score = 0.0

        # Base damage value
        score += damage * 2

        # Bonus for killing blow
        if target.hp <= damage:
            score += 50
            # Extra bonus if strategy wants kills
            if plan.strategy.value in ["aggressive_push", "desperate_rush"]:
                score += 20

        # Bonus for attacking focus targets
        if target in plan.focus_targets:
            score += 30

        # Bonus for attacking high-priority targets
        for priority_target, target_score in analysis.priority_targets[:3]:
            if priority_target == target:
                score += target_score * 0.5
                break

        # Penalty if attacker is vulnerable after attack
        attacker_pos = (attacker.y, attacker.x)
        if attacker_pos in analysis.threat_map:
            threat = analysis.threat_map[attacker_pos]
            # If we'll die from counterattack, reduce score
            if threat.threat_level >= attacker.hp:
                score -= 40
                # Unless it's desperate rush or we get the kill
                if plan.strategy.value == "desperate_rush" or target.hp <= damage:
                    score += 20  # Partially restore score for trades

        # Defensive strategy: only attack if safe
        if plan.strategy.value == "defensive_hold":
            if not self._is_attack_safe(attacker, analysis):
                score -= 30

        return score

    def _is_attack_safe(self, unit: 'Unit', analysis: 'BattlefieldAnalysis') -> bool:
        """
        Check if it's safe for unit to attack from current position.

        Args:
            unit: Unit considering attack
            analysis: Battlefield analysis

        Returns:
            True if attack is safe
        """
        pos = (unit.y, unit.x)
        if pos not in analysis.threat_map:
            return True

        threat = analysis.threat_map[pos]
        # Safe if threat is less than 40% of current HP
        return threat.threat_level < (unit.hp * 0.4)

    def _evaluate_moves(self, unit: 'Unit', analysis: 'BattlefieldAnalysis',
                       plan: 'StrategicPlan') -> List[Action]:
        """
        Evaluate movement actions.

        Args:
            unit: The unit to evaluate
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of move actions with scores
        """
        actions = []
        stats = unit.get_effective_stats()
        move_range = stats['move_range']

        # Get all reachable positions
        reachable = self._get_reachable_positions(unit, move_range)

        # Score each position
        for pos in reachable:
            score = self._score_move_position(unit, pos, analysis, plan)
            action = Action("move", target=pos, priority=score)
            actions.append(action)

        return actions

    def _get_reachable_positions(self, unit: 'Unit', move_range: int) -> List[Tuple[int, int]]:
        """
        Get all positions unit can move to (accounting for pathing around obstacles).

        Args:
            unit: The unit
            move_range: Movement range

        Returns:
            List of reachable (y, x) positions
        """
        reachable = []
        visited = set()
        queue = [(unit.y, unit.x, 0)]  # (y, x, steps_taken)
        visited.add((unit.y, unit.x))

        while queue:
            y, x, steps = queue.pop(0)

            # If we've used all our movement, stop expanding from this position
            if steps >= move_range:
                continue

            # Check all adjacent positions
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue

                    ny, nx = y + dy, x + dx

                    # Check bounds
                    if not (0 <= ny < self.game.map.height and 0 <= nx < self.game.map.width):
                        continue

                    # Skip if already visited
                    if (ny, nx) in visited:
                        continue

                    # Check if passable
                    if not self.game.map.is_passable(ny, nx):
                        continue

                    # Check if occupied
                    if self.game.get_unit_at(ny, nx) is not None:
                        continue

                    # Mark as visited
                    visited.add((ny, nx))

                    # Add to reachable (if not starting position)
                    if (ny, nx) != (unit.y, unit.x):
                        reachable.append((ny, nx))

                    # Add to queue for further expansion
                    queue.append((ny, nx, steps + 1))

        return reachable

    def _score_move_position(self, unit: 'Unit', position: Tuple[int, int],
                            analysis: 'BattlefieldAnalysis', plan: 'StrategicPlan') -> float:
        """
        Score a potential movement position.

        Args:
            unit: Unit considering move
            position: Target position (y, x)
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Position score
        """
        y, x = position
        score = 0.0

        # Safety evaluation
        threat = analysis.threat_map.get(position)
        if threat:
            threat_level = threat.threat_level
            # Heavy penalty if we'll die
            if threat_level >= unit.hp:
                score -= 100
            else:
                # Penalty proportional to threat
                score -= (threat_level / unit.hp) * 50

        # Defensive strategy: strongly prefer safe positions
        if plan.strategy.value == "defensive_hold":
            if not threat or threat.threat_level < unit.hp * 0.3:
                score += 20

        # Aggressive strategy: approach enemies (prefer positions with line of sight)
        if plan.strategy.value in ["aggressive_push", "desperate_rush"]:
            # Find closest enemy
            if analysis.enemy_units:
                min_distance = min(self.game.chess_distance(y, x, e.y, e.x)
                                 for e in analysis.enemy_units)
                # Closer = better (inverse distance bonus)
                score += max(15 - min_distance, 0)

                # BIG bonus if this position lets us see/attack an enemy
                stats = unit.get_effective_stats()
                attack_range = stats['attack_range']
                for enemy in analysis.enemy_units:
                    dist_to_enemy = self.game.chess_distance(y, x, enemy.y, enemy.x)
                    if dist_to_enemy <= attack_range:
                        # Check if we have line of sight from new position
                        if self.game.has_line_of_sight(y, x, enemy.y, enemy.x):
                            score += 30  # Major bonus for positions that enable attacks
                            break

        # Positioning strategy: move toward center
        if plan.strategy.value == "secure_position":
            center_y = self.game.map.height // 2
            center_x = self.game.map.width // 2
            distance_to_center = self.game.chess_distance(y, x, center_y, center_x)
            score += max(10 - distance_to_center, 0)

        # Bonus for supporting vulnerable allies
        for ally, _ in analysis.vulnerable_allies:
            distance_to_ally = self.game.chess_distance(y, x, ally.y, ally.x)
            if distance_to_ally <= 3:
                score += 10

        # Penalty for moving away from team
        if len(analysis.ai_units) > 1:
            other_allies = [u for u in analysis.ai_units if u != unit]
            avg_distance = sum(self.game.chess_distance(y, x, ally.y, ally.x)
                             for ally in other_allies) / len(other_allies)
            # Penalty if too far from team
            if avg_distance > 6:
                score -= 15

        return score

    def _evaluate_skills(self, unit: 'Unit', analysis: 'BattlefieldAnalysis',
                        plan: 'StrategicPlan') -> List[Action]:
        """
        Evaluate skill usage actions.

        Args:
            unit: The unit to evaluate
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of skill actions with scores
        """
        actions = []

        # Get available skills
        try:
            available_skills = unit.get_available_skills()
        except Exception as e:
            logger.error(f"Error getting skills for {unit.get_display_name()}: {e}")
            return actions

        # Evaluate each available skill
        for skill in available_skills:
            # Check if it's a self-targeted/AOE skill
            from boneglaive.game.skills import TargetType
            if hasattr(skill, 'target_type') and skill.target_type == TargetType.SELF:
                # Self-targeted AOE skills (e.g., Jawline)
                try:
                    if skill.can_use(unit, (unit.y, unit.x), self.game):
                        # Score based on number of enemies in AOE
                        score = self._score_aoe_skill_use(unit, skill, analysis, plan)
                        if score > 0:  # Only use if there are targets
                            action = Action("skill", target=(skill, unit), priority=score)
                            actions.append(action)
                except Exception:
                    continue
            else:
                # Enemy-targeted skills
                for enemy in analysis.enemy_units:
                    try:
                        if skill.can_use(unit, (enemy.y, enemy.x), self.game):
                            score = self._score_skill_use(unit, skill, enemy, analysis, plan)
                            action = Action("skill", target=(skill, enemy), priority=score)
                            actions.append(action)
                    except Exception:
                        continue

        return actions

    def _score_skill_use(self, unit: 'Unit', skill, target: 'Unit',
                        analysis: 'BattlefieldAnalysis', plan: 'StrategicPlan') -> float:
        """
        Score a skill usage. Enhanced to encourage more liberal skill usage.

        Args:
            unit: Unit using skill
            skill: The skill
            target: Target unit
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Skill usage score
        """
        # Higher base score - skills are generally better than basic attacks
        score = 50.0

        # Big bonus for focus targets
        if target in plan.focus_targets:
            score += 30

        # Aggressive strategies: use skills more
        if plan.strategy.value in ["aggressive_push", "desperate_rush"]:
            score += 20

        # Bonus for low HP enemies (skills can secure kills)
        if target.hp < target.max_hp * 0.4:
            score += 25

        # Bonus for high HP enemies (skills deal more damage)
        if target.hp > target.max_hp * 0.7:
            score += 15

        # Distance consideration - skills often have better range
        distance = self.game.chess_distance(unit.y, unit.x, target.y, target.x)
        stats = unit.get_effective_stats()
        attack_range = stats['attack_range']

        # Extra bonus if skill can hit from safer distance than basic attack
        if distance > attack_range:
            score += 20

        # Bonus based on target priority (high value targets)
        for priority_target, _ in analysis.priority_targets[:3]:
            if target == priority_target:
                score += 20
                break

        return score

    def _score_aoe_skill_use(self, unit: 'Unit', skill,
                            analysis: 'BattlefieldAnalysis', plan: 'StrategicPlan') -> float:
        """
        Score a self-targeted AOE skill (like Jawline).

        Args:
            unit: Unit using skill
            skill: The AOE skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Skill usage score (0 if no targets in range)
        """
        # Get AOE range/area (default to 1 tile radius)
        aoe_range = getattr(skill, 'area', 1)

        # Count enemies in AOE
        enemies_in_range = 0
        for enemy in analysis.enemy_units:
            distance = self.game.chess_distance(unit.y, unit.x, enemy.y, enemy.x)
            if distance <= aoe_range:
                enemies_in_range += 1

        # Don't use if no enemies in range
        if enemies_in_range == 0:
            return 0

        # Base score multiplied by number of targets
        score = 40.0 * enemies_in_range

        # Big bonus for hitting multiple enemies
        if enemies_in_range >= 2:
            score += 50
        if enemies_in_range >= 3:
            score += 30

        # Aggressive strategies: prefer AOE damage
        if plan.strategy.value in ["aggressive_push", "desperate_rush"]:
            score += 20

        return score

    def _evaluate_move_attack_combos(self, unit: 'Unit', analysis: 'BattlefieldAnalysis',
                                    plan: 'StrategicPlan') -> List[Action]:
        """
        Evaluate move + attack combinations.

        Args:
            unit: The unit to evaluate
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of combo actions with scores
        """
        actions = []
        stats = unit.get_effective_stats()
        move_range = stats['move_range']
        attack_range = stats['attack_range']
        damage = stats['attack']

        # Get reachable positions
        reachable = self._get_reachable_positions(unit, move_range)

        # For each position, check if we can attack from there
        for pos in reachable:
            y, x = pos

            for enemy in analysis.enemy_units:
                distance_from_new_pos = self.game.chess_distance(y, x, enemy.y, enemy.x)

                # Must be in attack range AND have line of sight
                if distance_from_new_pos <= attack_range and distance_from_new_pos > 0:
                    # Check line of sight from new position
                    if not self.game.has_line_of_sight(y, x, enemy.y, enemy.x):
                        continue  # Skip if blocked by walls

                    # Score the combo: position value + attack value
                    move_score = self._score_move_position(unit, pos, analysis, plan)
                    attack_score = self._score_attack(unit, enemy, analysis, plan, damage)

                    # Combo score is sum with a bonus
                    combo_score = move_score + attack_score + 10

                    action = Action("move_attack", target=(pos, enemy), priority=combo_score)
                    action.data['move_to'] = pos
                    action.data['attack_target'] = enemy
                    actions.append(action)

        return actions
