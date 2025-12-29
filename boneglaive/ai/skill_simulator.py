#!/usr/bin/env python3
"""
Skill Simulator for Smart AI.
Generic skill evaluation without hardcoded logic per unit.
"""

from typing import TYPE_CHECKING, Optional, Tuple, List
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.game.units import Unit
    from boneglaive.game.skills.core import ActiveSkill
    from boneglaive.ai.battlefield_analyzer import BattlefieldAnalysis
    from boneglaive.ai.strategic_planner import StrategicPlan


class SkillOutcome:
    """Represents the simulated outcome of using a skill."""

    def __init__(self):
        self.damage_dealt: int = 0
        self.healing_done: int = 0
        self.units_affected: List['Unit'] = []
        self.positioning_value: float = 0.0  # Value from repositioning
        self.status_effect_value: float = 0.0  # Value from status effects
        self.total_value: float = 0.0


class SkillSimulator:
    """
    Simulates skill outcomes without actually executing them.
    Provides generic skill evaluation for tactical decisions.
    """

    def __init__(self, game: 'Game', ai_player: int):
        """
        Initialize the skill simulator.

        Args:
            game: The game instance
            ai_player: The AI's player number
        """
        self.game = game
        self.ai_player = ai_player

    def simulate_skill(self, unit: 'Unit', skill: 'ActiveSkill', target_pos: Tuple[int, int],
                      analysis: 'BattlefieldAnalysis', plan: 'StrategicPlan') -> SkillOutcome:
        """
        Simulate using a skill and evaluate the outcome.

        Args:
            unit: Unit using the skill
            skill: The skill to use
            target_pos: Target position (y, x)
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Simulated outcome with value assessment
        """
        outcome = SkillOutcome()

        # Get skill properties from description/attributes
        skill_info = self._analyze_skill(skill)

        # Simulate damage
        if skill_info['deals_damage']:
            outcome.damage_dealt = self._estimate_skill_damage(unit, skill, target_pos)
            # Find affected units
            outcome.units_affected = self._get_affected_units(skill, target_pos)

        # Simulate healing
        if skill_info['heals']:
            outcome.healing_done = self._estimate_skill_healing(unit, skill, target_pos)

        # Evaluate positioning changes
        if skill_info['repositions']:
            outcome.positioning_value = self._evaluate_repositioning(unit, skill, target_pos, analysis)

        # Evaluate status effects
        if skill_info['applies_status']:
            outcome.status_effect_value = self._evaluate_status_effects(skill, target_pos, analysis, plan)

        # Calculate total value
        outcome.total_value = self._calculate_total_value(outcome, analysis, plan)

        return outcome

    def _analyze_skill(self, skill: 'ActiveSkill') -> dict:
        """
        Analyze skill properties from its attributes and description.

        Args:
            skill: The skill to analyze

        Returns:
            Dictionary of skill properties
        """
        info = {
            'deals_damage': False,
            'heals': False,
            'repositions': False,
            'applies_status': False,
            'is_aoe': False,
            'has_cooldown': skill.cooldown > 0
        }

        # Check skill description for keywords
        desc_lower = skill.description.lower() if hasattr(skill, 'description') else ""

        # Damage indicators
        if any(word in desc_lower for word in ['damage', 'attack', 'hit', 'strike', 'deals']):
            info['deals_damage'] = True

        # Healing indicators
        if any(word in desc_lower for word in ['heal', 'restore', 'regenerate']):
            info['heals'] = True

        # Repositioning indicators
        if any(word in desc_lower for word in ['move', 'teleport', 'push', 'pull', 'knock', 'vault', 'leap']):
            info['repositions'] = True

        # Status effect indicators
        if any(word in desc_lower for word in ['stun', 'slow', 'buff', 'debuff', 'effect', 'status']):
            info['applies_status'] = True

        # AOE indicators
        if any(word in desc_lower for word in ['area', 'aoe', 'all', 'nearby', 'radius', 'cone']):
            info['is_aoe'] = True

        return info

    def _estimate_skill_damage(self, unit: 'Unit', skill: 'ActiveSkill',
                               target_pos: Tuple[int, int]) -> int:
        """
        Estimate damage a skill will deal.

        Args:
            unit: Unit using skill
            skill: The skill
            target_pos: Target position

        Returns:
            Estimated damage
        """
        # Most skills use unit's attack stat as base
        stats = unit.get_effective_stats()
        base_damage = stats['attack']

        # Skills typically deal 1.0x to 1.5x attack damage
        # Use skill name/description to estimate multiplier
        multiplier = 1.2  # Default assumption

        skill_name_lower = skill.name.lower()

        # High damage skills
        if any(word in skill_name_lower for word in ['strike', 'blast', 'crush', 'smash']):
            multiplier = 1.5

        # Low damage skills
        if any(word in skill_name_lower for word in ['tap', 'poke', 'light']):
            multiplier = 0.8

        estimated_damage = int(base_damage * multiplier)

        logger.debug(f"Skill {skill.name} estimated damage: {estimated_damage}")
        return estimated_damage

    def _estimate_skill_healing(self, unit: 'Unit', skill: 'ActiveSkill',
                               target_pos: Tuple[int, int]) -> int:
        """
        Estimate healing a skill will provide.

        Args:
            unit: Unit using skill
            skill: The skill
            target_pos: Target position

        Returns:
            Estimated healing
        """
        # Healing skills typically restore 20-40 HP
        # This is a rough estimate
        return 30

    def _get_affected_units(self, skill: 'ActiveSkill', target_pos: Tuple[int, int]) -> List['Unit']:
        """
        Get list of units that would be affected by the skill.

        Args:
            skill: The skill
            target_pos: Target position

        Returns:
            List of affected units
        """
        affected = []
        target_unit = self.game.get_unit_at(target_pos[0], target_pos[1])

        if target_unit:
            affected.append(target_unit)

        # TODO: Handle AOE skills by checking nearby units
        # For now, just single target

        return affected

    def _evaluate_repositioning(self, unit: 'Unit', skill: 'ActiveSkill',
                               target_pos: Tuple[int, int],
                               analysis: 'BattlefieldAnalysis') -> float:
        """
        Evaluate value of repositioning from a skill.

        Args:
            unit: Unit using skill
            skill: The skill
            target_pos: Target position
            analysis: Battlefield analysis

        Returns:
            Repositioning value score
        """
        value = 0.0

        # Skills like Vault, Pry, etc. that move the user
        # Check if movement improves positioning

        # If skill moves user to target position
        threat_at_new_pos = analysis.threat_map.get(target_pos)
        current_threat = analysis.threat_map.get((unit.y, unit.x))

        # Value escaping danger
        if current_threat and (not threat_at_new_pos or threat_at_new_pos.threat_level < current_threat.threat_level):
            value += 20

        # Value getting closer to enemies for aggressive plays
        if analysis.enemy_units:
            current_min_dist = min(self.game.chess_distance(unit.y, unit.x, e.y, e.x)
                                  for e in analysis.enemy_units)
            new_min_dist = min(self.game.chess_distance(target_pos[0], target_pos[1], e.y, e.x)
                              for e in analysis.enemy_units)

            if new_min_dist < current_min_dist:
                value += 10  # Bonus for closing distance

        return value

    def _evaluate_status_effects(self, skill: 'ActiveSkill', target_pos: Tuple[int, int],
                                 analysis: 'BattlefieldAnalysis', plan: 'StrategicPlan') -> float:
        """
        Evaluate value of status effects from a skill.

        Args:
            skill: The skill
            target_pos: Target position
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Status effect value score
        """
        value = 0.0

        # Status effects are generally valuable
        # Debuffs on enemies worth more
        target_unit = self.game.get_unit_at(target_pos[0], target_pos[1])

        if target_unit:
            if target_unit.player != self.ai_player:
                # Debuff on enemy
                value += 15

                # Extra value if it's a focus target
                if target_unit in plan.focus_targets:
                    value += 10
            else:
                # Buff on ally
                value += 10

        return value

    def _calculate_total_value(self, outcome: SkillOutcome,
                               analysis: 'BattlefieldAnalysis',
                               plan: 'StrategicPlan') -> float:
        """
        Calculate total value of skill outcome.

        Args:
            outcome: The simulated outcome
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Total value score
        """
        value = 0.0

        # Damage value
        value += outcome.damage_dealt * 1.5  # Skills worth more than basic attacks

        # Killing blow bonus
        for unit in outcome.units_affected:
            if unit.player != self.ai_player and unit.hp <= outcome.damage_dealt:
                value += 40

        # Healing value
        value += outcome.healing_done * 1.2

        # Positioning value
        value += outcome.positioning_value

        # Status effect value
        value += outcome.status_effect_value

        # Cooldown penalty - skills with long cooldowns should be worth more when used
        # (inverse - don't waste them on low-value targets)

        outcome.total_value = value
        return value

    def score_skill_action(self, unit: 'Unit', skill: 'ActiveSkill',
                          target_pos: Tuple[int, int],
                          analysis: 'BattlefieldAnalysis',
                          plan: 'StrategicPlan') -> float:
        """
        Score a skill usage action.

        Args:
            unit: Unit using skill
            skill: The skill
            target_pos: Target position
            analysis: Battlefield analysis
            plan: Strategic plan

        Returns:
            Skill usage score
        """
        # Simulate the skill
        outcome = self.simulate_skill(unit, skill, target_pos, analysis, plan)

        # Base score is the total value
        score = outcome.total_value

        # Strategy modifiers
        if plan.strategy.value in ['aggressive_push', 'desperate_rush']:
            # Boost damage-dealing skills
            if outcome.damage_dealt > 0:
                score *= 1.2

        if plan.strategy.value == 'defensive_hold':
            # Boost defensive/healing skills
            if outcome.healing_done > 0:
                score *= 1.3

        logger.debug(f"Skill {skill.name} scored: {score:.1f} (damage: {outcome.damage_dealt}, "
                    f"healing: {outcome.healing_done})")

        return score
