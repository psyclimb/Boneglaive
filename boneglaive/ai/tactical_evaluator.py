#!/usr/bin/env python3
"""
Tactical Evaluator for Smart AI.
Scores individual unit actions to find optimal choices.
"""

from typing import TYPE_CHECKING, List, Tuple, Optional, Dict
from boneglaive.utils.debug import logger
from boneglaive.game.skills import TargetType

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

            # Check range and line of sight
            if distance <= attack_range and distance > 0:
                # Verify line of sight is not blocked by terrain or units
                if not self.game.has_line_of_sight(unit.y, unit.x, enemy.y, enemy.x):
                    continue  # Skip this enemy - no LOS

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
            # Check for skills requiring special AI handling
            if skill.name == "Site Inspection":
                try:
                    site_inspection_actions = self._evaluate_site_inspection(unit, skill, analysis, plan)
                    actions.extend(site_inspection_actions)
                    logger.debug(f"        Site Inspection: Found {len(site_inspection_actions)} actions")
                except Exception as e:
                    logger.error(f"        Error evaluating Site Inspection: {e}")
                continue
            elif skill.name == "Marrow Dike":
                try:
                    dike_actions = self._evaluate_marrow_dike(unit, skill, analysis, plan)
                    actions.extend(dike_actions)
                    logger.debug(f"        Marrow Dike: Found {len(dike_actions)} actions")
                except Exception as e:
                    logger.error(f"        Error evaluating Marrow Dike: {e}")
                continue
            elif skill.name == "Gaussian Dusk":
                try:
                    gaussian_actions = self._evaluate_gaussian_dusk(unit, skill, analysis, plan)
                    actions.extend(gaussian_actions)
                    logger.debug(f"        Gaussian Dusk: Found {len(gaussian_actions)} directional actions")
                except Exception as e:
                    logger.error(f"        Error evaluating Gaussian Dusk: {e}")
                continue

            # Check for ally-targeted skills (DERELICTIONIST)
            if hasattr(skill, 'target_type') and skill.target_type == TargetType.ALLY:
                if skill.name == "Vagal Run":
                    try:
                        vagal_actions = self._evaluate_vagal_run(unit, skill, analysis, plan)
                        actions.extend(vagal_actions)
                        logger.debug(f"        Vagal Run: Found {len(vagal_actions)} ally targets")
                    except Exception as e:
                        logger.error(f"        Error evaluating Vagal Run: {e}")
                    continue
                elif skill.name == "Derelict":
                    try:
                        derelict_actions = self._evaluate_derelict(unit, skill, analysis, plan)
                        actions.extend(derelict_actions)
                        logger.debug(f"        Derelict: Found {len(derelict_actions)} ally targets")
                    except Exception as e:
                        logger.error(f"        Error evaluating Derelict: {e}")
                    continue
                elif skill.name == "Partition":
                    try:
                        partition_actions = self._evaluate_partition(unit, skill, analysis, plan)
                        actions.extend(partition_actions)
                        logger.debug(f"        Partition: Found {len(partition_actions)} ally targets")
                    except Exception as e:
                        logger.error(f"        Error evaluating Partition: {e}")
                    continue

            # Check if it's a self-targeted/AOE skill
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

    def _evaluate_site_inspection(self, unit: 'Unit', skill, analysis: 'BattlefieldAnalysis',
                                   plan: 'StrategicPlan') -> List[Action]:
        """
        Special evaluation for Site Inspection skill (MANDIBLE FOREMAN).

        Site Inspection buffs allies in a 3x3 area based on terrain:
        - 0 impassable terrain: +1 attack, +1 movement
        - 1 impassable terrain: +1 attack only
        - 2+ impassable terrain: no effect

        Args:
            unit: The MANDIBLE FOREMAN unit
            skill: The Site Inspection skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of Site Inspection actions with scores
        """
        actions = []
        skill_range = getattr(skill, 'range', 3)

        # Get all friendly units (including self)
        friendly_units = [u for u in self.game.units if u.player == unit.player and u.is_alive()]

        if not friendly_units:
            return actions

        # Evaluate potential target positions within range
        for target_y in range(max(0, unit.y - skill_range), min(self.game.map.height, unit.y + skill_range + 1)):
            for target_x in range(max(0, unit.x - skill_range), min(self.game.map.width, unit.x + skill_range + 1)):
                # Check if position is in range
                distance = self.game.chess_distance(unit.y, unit.x, target_y, target_x)
                if distance > skill_range:
                    continue

                # Check if skill can be used at this position
                try:
                    if not skill.can_use(unit, (target_y, target_x), self.game):
                        continue
                except Exception:
                    continue

                # Analyze the 3x3 area around target position
                allies_in_area = []
                impassable_count = 0

                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        check_y = target_y + dy
                        check_x = target_x + dx

                        # Check bounds
                        if not self.game.is_valid_position(check_y, check_x):
                            continue

                        # Count impassable terrain
                        if not self.game.map.is_passable(check_y, check_x):
                            impassable_count += 1

                        # Check for friendly units
                        ally = self.game.get_unit_at(check_y, check_x)
                        if ally and ally.player == unit.player:
                            allies_in_area.append(ally)

                # Skip if no allies in area or too much terrain
                if not allies_in_area or impassable_count >= 2:
                    continue

                # Calculate score
                score = 0.0

                # Base score for number of allies buffed
                unbuffed_allies = 0
                for ally in allies_in_area:
                    # Check if ally already has Site Inspection buff
                    has_full = hasattr(ally, 'status_site_inspection') and ally.status_site_inspection
                    has_partial = hasattr(ally, 'status_site_inspection_partial') and ally.status_site_inspection_partial

                    if not has_full and not has_partial:
                        unbuffed_allies += 1
                        score += 30  # Good value for buffing new ally
                    elif has_partial and impassable_count == 0:
                        score += 15  # Decent value for upgrading partial to full
                    elif has_full or has_partial:
                        score += 5   # Small value for refreshing existing buff

                # Bonus for hitting multiple allies
                if len(allies_in_area) >= 2:
                    score += 20
                if len(allies_in_area) >= 3:
                    score += 15

                # Terrain penalty (reduces effectiveness)
                if impassable_count == 1:
                    score -= 10  # Partial buff is less valuable

                # Strategy bonuses
                if plan.strategy.value in ["aggressive_push", "desperate_rush"]:
                    # Prefer buffing in aggressive situations
                    score += 15
                elif plan.strategy.value == "defensive_hold":
                    # Still good for defense
                    score += 10

                # Bonus for buffing high-priority units or focus targets
                for ally in allies_in_area:
                    if ally in plan.focus_targets:
                        score += 10

                # Only create action if score is worthwhile
                if score > 20:
                    action = Action("skill", target=(skill, (target_y, target_x)), priority=score)
                    action.data['target_pos'] = (target_y, target_x)
                    action.data['allies_affected'] = len(allies_in_area)
                    action.data['unbuffed_count'] = unbuffed_allies
                    actions.append(action)

        return actions

    def _evaluate_marrow_dike(self, unit: 'Unit', skill, analysis: 'BattlefieldAnalysis',
                              plan: 'StrategicPlan') -> List[Action]:
        """
        Special evaluation for Marrow Dike skill (MARROW CONDENSER).

        Marrow Dike creates a 5x5 perimeter wall around the caster:
        - Blocks movement and line of sight
        - Pulls units on perimeter inside
        - When upgraded: enemies inside get -1 movement

        Use cases:
        - Defensive: Protect vulnerable allies
        - Offensive: Trap and control enemies

        Args:
            unit: The MARROW CONDENSER unit
            skill: The Marrow Dike skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of Marrow Dike actions with scores
        """
        actions = []

        # Check if skill is usable
        try:
            if not skill.can_use(unit, (unit.y, unit.x), self.game):
                return actions
        except Exception:
            return actions

        # Analyze the 5x5 area around unit
        center_y, center_x = unit.y, unit.x

        # Count units that would be affected
        allies_inside = []
        enemies_inside = []
        allies_endangered = []

        for dy in range(-2, 3):
            for dx in range(-2, 3):
                check_y = center_y + dy
                check_x = center_x + dx

                # Skip out of bounds
                if not self.game.is_valid_position(check_y, check_x):
                    continue

                # Skip center (unit's own position)
                if dy == 0 and dx == 0:
                    continue

                other_unit = self.game.get_unit_at(check_y, check_x)
                if not other_unit:
                    continue

                # Interior tiles (not on perimeter)
                is_interior = abs(dy) < 2 and abs(dx) < 2

                if other_unit.player == unit.player:
                    # Friendly unit
                    allies_inside.append(other_unit)

                    # Check if ally is endangered (in threat map)
                    ally_pos = (other_unit.y, other_unit.x)
                    if ally_pos in analysis.threat_map:
                        threat = analysis.threat_map[ally_pos]
                        if threat.threat_level >= other_unit.hp * 0.5:  # Significant threat
                            allies_endangered.append(other_unit)
                else:
                    # Enemy unit
                    enemies_inside.append(other_unit)

        # Calculate score based on tactical situation
        score = 0.0

        # DEFENSIVE SCORING: Protect endangered allies
        if allies_endangered:
            score += len(allies_endangered) * 40
            logger.debug(f"  Marrow Dike: {len(allies_endangered)} allies endangered, +{len(allies_endangered) * 40} score")

        # OFFENSIVE SCORING: Trap enemies
        if enemies_inside:
            enemy_score = 0
            for enemy in enemies_inside:
                # Base value for trapping
                enemy_score += 50

                # Bonus for priority targets
                if enemy in [t for t, s in analysis.priority_targets[:3]]:
                    enemy_score += 30

                # Bonus for low HP enemies (easier to finish off)
                if enemy.hp < enemy.max_hp * 0.4:
                    enemy_score += 20

            score += enemy_score
            logger.debug(f"  Marrow Dike: {len(enemies_inside)} enemies trapped, +{enemy_score} score")

        # PENALTY: Too many allies trapped disadvantageously
        # (More than 2 allies and no enemies = probably bad positioning)
        if len(allies_inside) > 2 and len(enemies_inside) == 0:
            penalty = len(allies_inside) * 15
            score -= penalty
            logger.debug(f"  Marrow Dike: {len(allies_inside)} allies trapped with no enemies, -{penalty} score")

        # POSITIONING BONUSES
        # Near center of map (better control)
        center_map_y = self.game.map.height // 2
        center_map_x = self.game.map.width // 2
        distance_to_center = self.game.chess_distance(unit.y, unit.x, center_map_y, center_map_x)
        if distance_to_center <= 3:
            score += 10
            logger.debug(f"  Marrow Dike: Near map center, +10 score")

        # STRATEGY BONUSES
        if plan.strategy.value == "defensive_hold":
            # Boost defensive usage
            if allies_endangered:
                score += 25
                logger.debug(f"  Marrow Dike: Defensive strategy + endangered allies, +25 score")
        elif plan.strategy.value in ["aggressive_push", "desperate_rush"]:
            # Boost offensive usage
            if enemies_inside:
                score += 20
                logger.debug(f"  Marrow Dike: Aggressive strategy + enemies trapped, +20 score")

        # UNIT CONDITION BONUSES
        # Low HP = prefer defensive usage
        if unit.hp < unit.max_hp * 0.5:
            score += 20
            logger.debug(f"  Marrow Dike: Unit low HP, +20 score")

        # Minimum threshold - don't use unless it's tactically valuable
        if score > 40:
            action = Action("skill", target=(skill, unit), priority=score)
            action.data['enemies_trapped'] = len(enemies_inside)
            action.data['allies_protected'] = len(allies_endangered)
            action.data['total_allies'] = len(allies_inside)
            actions.append(action)
            logger.debug(f"  Marrow Dike: Created action with score {score}")
        else:
            logger.debug(f"  Marrow Dike: Score {score} below threshold, skipping")

        return actions

    def _evaluate_gaussian_dusk(self, unit: 'Unit', skill, analysis: 'BattlefieldAnalysis',
                                 plan: 'StrategicPlan') -> List[Action]:
        """
        Special evaluation for Gaussian Dusk skill (FOWL_CONTRIVANCE).

        Gaussian Dusk fires a piercing rail gun shot in a cardinal direction:
        - Only fires in N, S, E, W (no diagonals)
        - Hits ALL enemies in a straight line across the map
        - Deals 9 damage (ignores defense)
        - Destroys terrain
        - 5-turn cooldown + 1-turn recharge lockout

        The AI must evaluate all 4 cardinal directions and pick the best line.

        Args:
            unit: The FOWL_CONTRIVANCE unit
            skill: The Gaussian Dusk skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of Gaussian Dusk actions (one per viable direction)
        """
        actions = []

        # Check if skill is usable
        try:
            if not skill.can_use(unit, (unit.y, unit.x), self.game):
                return actions
        except Exception:
            return actions

        # Get skill damage
        damage = getattr(skill, 'damage', 9)

        # Four cardinal directions: (name, (dy, dx))
        directions = [
            ('NORTH', (-1, 0)),
            ('SOUTH', (1, 0)),
            ('EAST', (0, 1)),
            ('WEST', (0, -1))
        ]

        # Evaluate each cardinal direction
        for dir_name, (dy, dx) in directions:
            # Trace line from unit position in this direction
            enemies_in_line = []
            y, x = unit.y, unit.x

            # Follow the line to map edge
            while True:
                # Move one step in direction
                y += dy
                x += dx

                # Check if still in bounds
                if not self.game.is_valid_position(y, x):
                    break

                # Check for enemy unit
                enemy = self.game.get_unit_at(y, x)
                if enemy and enemy.player != unit.player and enemy.is_alive():
                    enemies_in_line.append(enemy)

            # Skip if no enemies in this direction
            if not enemies_in_line:
                logger.debug(f"  Gaussian Dusk {dir_name}: No enemies")
                continue

            # Calculate score for this direction
            score = 0.0

            # Base score per enemy hit
            score += len(enemies_in_line) * 50
            logger.debug(f"  Gaussian Dusk {dir_name}: {len(enemies_in_line)} enemies, +{len(enemies_in_line) * 50} base")

            # Bonus for killing blows
            kills = 0
            for enemy in enemies_in_line:
                if enemy.hp <= damage:
                    kills += 1
                    score += 30
            if kills > 0:
                logger.debug(f"  Gaussian Dusk {dir_name}: {kills} kills, +{kills * 30} bonus")

            # Bonus for priority targets
            priority_hits = 0
            for enemy in enemies_in_line:
                if enemy in [t for t, s in analysis.priority_targets[:3]]:
                    priority_hits += 1
                    score += 40
            if priority_hits > 0:
                logger.debug(f"  Gaussian Dusk {dir_name}: {priority_hits} priority targets, +{priority_hits * 40} bonus")

            # Bonus for hitting multiple enemies (efficient use)
            if len(enemies_in_line) >= 2:
                multi_bonus = 25
                score += multi_bonus
                logger.debug(f"  Gaussian Dusk {dir_name}: Multi-hit, +{multi_bonus} bonus")

            if len(enemies_in_line) >= 3:
                extra_bonus = 20
                score += extra_bonus
                logger.debug(f"  Gaussian Dusk {dir_name}: 3+ enemies, +{extra_bonus} bonus")

            # Strategy bonuses
            if plan.strategy.value in ["aggressive_push", "desperate_rush"]:
                strategy_bonus = 20
                score += strategy_bonus
                logger.debug(f"  Gaussian Dusk {dir_name}: Aggressive strategy, +{strategy_bonus} bonus")

            # Bonus for hitting low HP enemies (easier to finish off)
            low_hp_targets = sum(1 for e in enemies_in_line if e.hp < e.max_hp * 0.4)
            if low_hp_targets > 0:
                low_hp_bonus = low_hp_targets * 15
                score += low_hp_bonus
                logger.debug(f"  Gaussian Dusk {dir_name}: {low_hp_targets} low HP, +{low_hp_bonus} bonus")

            # Create target position far in this direction
            # This ensures the skill will snap to the desired cardinal direction
            far_distance = 50  # Arbitrary large distance
            target_y = unit.y + (dy * far_distance)
            target_x = unit.x + (dx * far_distance)

            # Clamp to map bounds
            target_y = max(0, min(self.game.map.height - 1, target_y))
            target_x = max(0, min(self.game.map.width - 1, target_x))

            target_pos = (target_y, target_x)

            # Create action for this direction
            action = Action("skill", target=(skill, target_pos), priority=score)
            action.data['direction'] = dir_name
            action.data['enemies_hit'] = len(enemies_in_line)
            action.data['kills'] = kills
            action.data['target_pos'] = target_pos
            actions.append(action)

            logger.debug(f"  Gaussian Dusk {dir_name}: Total score {score}")

        return actions

    def _evaluate_vagal_run(self, unit: 'Unit', skill, analysis: 'BattlefieldAnalysis',
                             plan: 'StrategicPlan') -> List[Action]:
        """
        Special evaluation for Vagal Run skill (DERELICTIONIST).

        Vagal Run cleanses status effects and deals/heals based on distance:
        - Close range (3-6): Deals piercing damage
        - Far range (7+): Heals
        - Clears all status effects
        - Delayed abreaction after 3 turns

        Args:
            unit: The DERELICTIONIST unit
            skill: The Vagal Run skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of Vagal Run actions targeting allies
        """
        actions = []
        skill_range = getattr(skill, 'range', 3)

        # Get all friendly units (excluding self)
        friendly_units = [u for u in self.game.units
                         if u.player == unit.player and u.is_alive() and u != unit]

        if not friendly_units:
            return actions

        # Harmful status effects that Vagal Run cleanses
        harmful_statuses = [
            'trapped_by', 'mired', 'jawline_affected', 'trauma_debt',
            'estranged', 'auction_curse', 'gaussian_dusk_recharge'
        ]

        # Evaluate each ally
        for ally in friendly_units:
            # Check range
            distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)
            if distance > skill_range:
                continue

            # Check if skill can be used
            try:
                if not skill.can_use(unit, (ally.y, ally.x), self.game):
                    continue
            except Exception:
                continue

            # Check if ally already has vagal run active
            if hasattr(ally, 'vagal_run_active') and ally.vagal_run_active:
                continue

            # Calculate score
            score = 0.0

            # Count harmful status effects
            status_count = 0
            critical_statuses = 0
            for status in harmful_statuses:
                if hasattr(ally, status):
                    status_value = getattr(ally, status)
                    if status_value and status_value is not False and status_value != 0:
                        status_count += 1
                        # Critical statuses (trapped, mired)
                        if status in ['trapped_by', 'mired', 'jawline_affected']:
                            critical_statuses += 1

            # Base score for cleansing
            if status_count > 0:
                score += status_count * 40
                logger.debug(f"  Vagal Run on {ally.get_display_name()}: {status_count} statuses, +{status_count * 40}")

            # Bonus for critical statuses
            if critical_statuses > 0:
                crit_bonus = critical_statuses * 60
                score += crit_bonus
                logger.debug(f"  Vagal Run on {ally.get_display_name()}: {critical_statuses} critical statuses, +{crit_bonus}")

            # Calculate healing/damage value based on final distance after DERELICTIONIST moves
            source_y, source_x = unit.y, unit.x
            if unit.move_target:
                source_y, source_x = unit.move_target
            final_distance = self.game.chess_distance(source_y, source_x, ally.y, ally.x)

            # Close range (3-6): Damage component
            if 3 <= final_distance <= 6:
                damage = min(3, max(0, 6 - final_distance))
                # Small score - damage isn't usually desirable on allies
                # But if ally needs status cleared, this is acceptable
                if status_count > 0:
                    score += 10  # Worth using even though it damages
                    logger.debug(f"  Vagal Run on {ally.get_display_name()}: Close range damage acceptable with statuses, +10")
            # Far range (7+): Healing component
            elif final_distance >= 7:
                heal_amount = final_distance - 6
                hp_missing = ally.max_hp - ally.hp
                actual_heal = min(heal_amount, hp_missing)
                if actual_heal > 0:
                    heal_score = actual_heal * 2
                    score += heal_score
                    logger.debug(f"  Vagal Run on {ally.get_display_name()}: Healing {actual_heal} HP, +{heal_score}")

            # Bonus if ally is endangered
            ally_pos = (ally.y, ally.x)
            if ally_pos in analysis.threat_map:
                threat = analysis.threat_map[ally_pos]
                if threat.threat_level >= ally.hp * 0.5:
                    endangered_bonus = 40
                    score += endangered_bonus
                    logger.debug(f"  Vagal Run on {ally.get_display_name()}: Endangered, +{endangered_bonus}")

            # Bonus for priority units
            if ally in plan.focus_targets:
                priority_bonus = 30
                score += priority_bonus
                logger.debug(f"  Vagal Run on {ally.get_display_name()}: Priority target, +{priority_bonus}")

            # Only create action if worthwhile
            if score > 30:
                action = Action("skill", target=(skill, ally), priority=score)
                action.data['ally_target'] = ally
                action.data['statuses_cleared'] = status_count
                actions.append(action)
                logger.debug(f"  Vagal Run on {ally.get_display_name()}: Total score {score}")

        return actions

    def _evaluate_derelict(self, unit: 'Unit', skill, analysis: 'BattlefieldAnalysis',
                           plan: 'StrategicPlan') -> List[Action]:
        """
        Special evaluation for Derelict skill (DERELICTIONIST).

        Derelict pushes ally 4 tiles away:
        - Ally heals for distance from DERELICTIONIST after push
        - Ally becomes immobilized for 1 turn
        - Used to rescue endangered allies or reposition

        Args:
            unit: The DERELICTIONIST unit
            skill: The Derelict skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of Derelict actions targeting allies
        """
        actions = []
        skill_range = getattr(skill, 'range', 3)
        push_distance = 4

        # Get all friendly units (excluding self)
        friendly_units = [u for u in self.game.units
                         if u.player == unit.player and u.is_alive() and u != unit]

        if not friendly_units:
            return actions

        # Evaluate each ally
        for ally in friendly_units:
            # Check range
            distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)
            if distance > skill_range:
                continue

            # Check if skill can be used
            try:
                if not skill.can_use(unit, (ally.y, ally.x), self.game):
                    continue
            except Exception:
                continue

            # Calculate push direction
            dy = ally.y - unit.y
            dx = ally.x - unit.x

            # Normalize direction
            if dy != 0:
                dy = 1 if dy > 0 else -1
            if dx != 0:
                dx = 1 if dx > 0 else -1

            # Simulate push to find landing position
            landing_y, landing_x = ally.y, ally.x
            tiles_pushed = 0

            for step in range(push_distance):
                next_y = landing_y + dy
                next_x = landing_x + dx

                # Check if position is valid and passable
                if not self.game.is_valid_position(next_y, next_x):
                    break
                if not self.game.map.is_passable(next_y, next_x):
                    break
                # Check if occupied by another unit
                if self.game.get_unit_at(next_y, next_x):
                    break

                landing_y = next_y
                landing_x = next_x
                tiles_pushed += 1

            # If couldn't push at all, skip
            if tiles_pushed == 0:
                continue

            # Calculate score
            score = 0.0

            # Check if ally is currently endangered
            ally_pos = (ally.y, ally.x)
            endangered = False
            current_threat = 0
            if ally_pos in analysis.threat_map:
                threat = analysis.threat_map[ally_pos]
                current_threat = threat.threat_level
                if current_threat >= ally.hp * 0.5:
                    endangered = True

            # Count enemies near current position
            enemies_near_current = 0
            for enemy in analysis.enemy_units:
                if self.game.chess_distance(ally.y, ally.x, enemy.y, enemy.x) <= 2:
                    enemies_near_current += 1

            # Check landing zone safety
            landing_pos = (landing_y, landing_x)
            landing_threat = 0
            if landing_pos in analysis.threat_map:
                threat = analysis.threat_map[landing_pos]
                landing_threat = threat.threat_level

            # Count enemies near landing position
            enemies_near_landing = 0
            for enemy in analysis.enemy_units:
                if self.game.chess_distance(landing_y, landing_x, enemy.y, enemy.x) <= 2:
                    enemies_near_landing += 1

            # Rescue scoring: High value if moving ally from danger to safety
            if endangered and landing_threat < current_threat * 0.5:
                rescue_score = 80
                score += rescue_score
                logger.debug(f"  Derelict on {ally.get_display_name()}: Rescue from danger, +{rescue_score}")

            # Bonus for each enemy near current position (escaping)
            if enemies_near_current > 0:
                escape_score = enemies_near_current * 15
                score += escape_score
                logger.debug(f"  Derelict on {ally.get_display_name()}: Escaping {enemies_near_current} enemies, +{escape_score}")

            # Penalty if landing zone has more enemies
            if enemies_near_landing > enemies_near_current:
                penalty = (enemies_near_landing - enemies_near_current) * 20
                score -= penalty
                logger.debug(f"  Derelict on {ally.get_display_name()}: Landing near more enemies, -{penalty}")

            # Healing value: Calculate final distance and healing
            # After push, calculate distance from DERELICTIONIST to landing position
            final_distance = self.game.chess_distance(unit.y, unit.x, landing_y, landing_x)
            heal_amount = final_distance
            hp_missing = ally.max_hp - ally.hp
            actual_heal = min(heal_amount, hp_missing)

            if actual_heal > 0:
                heal_score = actual_heal * 3
                score += heal_score
                logger.debug(f"  Derelict on {ally.get_display_name()}: Healing {actual_heal} HP, +{heal_score}")

            # Bonus for safe landing zone
            if landing_threat < ally.hp * 0.3:
                safe_landing = 30
                score += safe_landing
                logger.debug(f"  Derelict on {ally.get_display_name()}: Safe landing zone, +{safe_landing}")

            # Penalty for immobilization (ally can't move next turn)
            # Only significant if ally is in danger at landing position
            if landing_threat > ally.hp * 0.3:
                immobile_penalty = 40
                score -= immobile_penalty
                logger.debug(f"  Derelict on {ally.get_display_name()}: Immobilized in danger, -{immobile_penalty}")

            # Bonus for priority units
            if ally in plan.focus_targets:
                priority_bonus = 25
                score += priority_bonus
                logger.debug(f"  Derelict on {ally.get_display_name()}: Priority target, +{priority_bonus}")

            # Strategy bonuses
            if plan.strategy.value == "defensive_hold" and endangered:
                defensive_bonus = 20
                score += defensive_bonus
                logger.debug(f"  Derelict on {ally.get_display_name()}: Defensive rescue, +{defensive_bonus}")

            # Only create action if worthwhile
            if score > 40:
                action = Action("skill", target=(skill, ally), priority=score)
                action.data['ally_target'] = ally
                action.data['landing_pos'] = (landing_y, landing_x)
                action.data['healing'] = actual_heal
                actions.append(action)
                logger.debug(f"  Derelict on {ally.get_display_name()}: Total score {score}")

        return actions

    def _evaluate_partition(self, unit: 'Unit', skill, analysis: 'BattlefieldAnalysis',
                            plan: 'StrategicPlan') -> List[Action]:
        """
        Special evaluation for Partition skill (DERELICTIONIST).

        Partition grants ally damage reduction shield:
        - Blocks 1 damage from all sources for 3 turns
        - Emergency intervention: Blocks fatal damage, teleports DERELICTIONIST
        - Proactive defensive support

        Args:
            unit: The DERELICTIONIST unit
            skill: The Partition skill
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            List of Partition actions targeting allies
        """
        actions = []
        skill_range = getattr(skill, 'range', 3)

        # Get all friendly units (excluding self if desired)
        friendly_units = [u for u in self.game.units
                         if u.player == unit.player and u.is_alive()]

        if not friendly_units:
            return actions

        # Evaluate each ally
        for ally in friendly_units:
            # Check range
            distance = self.game.chess_distance(unit.y, unit.x, ally.y, ally.x)
            if distance > skill_range:
                continue

            # Check if skill can be used
            try:
                if not skill.can_use(unit, (ally.y, ally.x), self.game):
                    continue
            except Exception:
                continue

            # Check if ally already has partition shield
            if hasattr(ally, 'partition_shield_active') and ally.partition_shield_active:
                continue

            # Calculate score
            score = 0.0

            # Check threat level at ally position
            ally_pos = (ally.y, ally.x)
            endangered = False
            threat_level = 0
            if ally_pos in analysis.threat_map:
                threat = analysis.threat_map[ally_pos]
                threat_level = threat.threat_level
                if threat_level >= ally.hp * 0.5:
                    endangered = True

            # High score for endangered allies
            if endangered:
                endangered_score = 100
                score += endangered_score
                logger.debug(f"  Partition on {ally.get_display_name()}: Endangered (threat {threat_level}), +{endangered_score}")

            # Bonus for low HP allies (preemptive protection)
            if ally.hp < ally.max_hp * 0.4:
                low_hp_score = 50
                score += low_hp_score
                logger.debug(f"  Partition on {ally.get_display_name()}: Low HP ({ally.hp}/{ally.max_hp}), +{low_hp_score}")

            # Bonus for priority units
            if ally in plan.focus_targets:
                priority_score = 60
                score += priority_score
                logger.debug(f"  Partition on {ally.get_display_name()}: Priority target, +{priority_score}")

            # Bonus for key unit types (DERELICTIONIST itself, high-value units)
            if ally == unit:
                # Shielding self
                self_shield = 40
                score += self_shield
                logger.debug(f"  Partition on {ally.get_display_name()}: Self-shield, +{self_shield}")
            elif hasattr(ally, 'type'):
                from boneglaive.utils.constants import UnitType
                # Protect other DERELICTIONISTs or key support units
                if ally.type in [UnitType.DERELICTIONIST, UnitType.POTPOURRIST]:
                    support_bonus = 40
                    score += support_bonus
                    logger.debug(f"  Partition on {ally.get_display_name()}: Support unit, +{support_bonus}")

            # Estimate damage reduction value
            # Shield blocks 1 damage per hit for 3 turns
            # Estimate number of hits ally will take
            enemies_in_range = 0
            for enemy in analysis.enemy_units:
                enemy_stats = enemy.get_effective_stats()
                enemy_range = enemy_stats.get('attack_range', 1)
                if self.game.chess_distance(ally.y, ally.x, enemy.y, enemy.x) <= enemy_range:
                    enemies_in_range += 1

            if enemies_in_range > 0:
                # Estimate shield will block 1 damage per enemy per turn for 3 turns
                estimated_blocks = min(enemies_in_range * 3, 9)  # Cap at 9 damage blocked
                shield_value = estimated_blocks * 5
                score += shield_value
                logger.debug(f"  Partition on {ally.get_display_name()}: {enemies_in_range} enemies in range, estimated {estimated_blocks} blocks, +{shield_value}")

            # Strategy bonuses
            if plan.strategy.value == "defensive_hold":
                defensive_bonus = 25
                score += defensive_bonus
                logger.debug(f"  Partition on {ally.get_display_name()}: Defensive strategy, +{defensive_bonus}")

            # Penalty for full HP allies in safe positions (wasteful)
            if ally.hp == ally.max_hp and threat_level < ally.hp * 0.2:
                waste_penalty = 30
                score -= waste_penalty
                logger.debug(f"  Partition on {ally.get_display_name()}: Full HP and safe, -{waste_penalty}")

            # Bonus for allies about to engage
            # (Moving toward enemies)
            if hasattr(ally, 'move_target') and ally.move_target:
                # Ally is moving - likely engaging
                engaging_bonus = 15
                score += engaging_bonus
                logger.debug(f"  Partition on {ally.get_display_name()}: Engaging/moving, +{engaging_bonus}")

            # Only create action if worthwhile
            if score > 40:
                action = Action("skill", target=(skill, ally), priority=score)
                action.data['ally_target'] = ally
                action.data['threat_level'] = threat_level
                action.data['endangered'] = endangered
                actions.append(action)
                logger.debug(f"  Partition on {ally.get_display_name()}: Total score {score}")

        return actions
