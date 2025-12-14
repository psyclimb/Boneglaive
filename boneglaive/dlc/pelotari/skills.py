#!/usr/bin/env python3
"""
Skills for PELOTARI DLC unit.

The PELOTARI is a jai alai specialist with ricochet ball mechanics and frequency modulation.
"""

import random
from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Riposte(PassiveSkill):
    """
    Passive skill for PELOTARI.
    Grants +2 attack range. Refreshes every 3 turns.
    When knocked off, converts to spread shot (6 balls, 4 damage each, 120° cone).
    """

    def __init__(self):
        super().__init__(
            name="Riposte",
            key="R",
            description="Grants +2 attack range. Refreshes every 3 turns. When knocked off, converts to 120° spread shot."
        )
        self.range_bonus = 2
        self.refresh_turns = 3
        self.turns_until_refresh = 0

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """
        Apply Riposte passive effect.
        Grants +2 range and handles buff refresh timing.
        """
        if not game:
            return

        # Initialize buff state if needed
        if not hasattr(user, 'riposte_buff_active'):
            user.riposte_buff_active = True  # Start with buff active
            user.riposte_turns_without_buff = 0
            user.attack_range_bonus = self.range_bonus
            logger.debug(f"{user.get_display_name()} starts with Riposte buff (+{self.range_bonus} range)")

        # Track turns for refresh
        if not user.riposte_buff_active:
            user.riposte_turns_without_buff += 1
            if user.riposte_turns_without_buff >= self.refresh_turns:
                # Refresh buff
                user.riposte_buff_active = True
                user.riposte_turns_without_buff = 0
                user.attack_range_bonus = self.range_bonus
                message_log.add_message(
                    f"{user.get_display_name()}'s Riposte buff refreshes",
                    MessageType.ABILITY,
                    player=user.player
                )
                logger.debug(f"{user.get_display_name()} Riposte buff refreshed")

    def knock_off_buff(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """
        Knock off the Riposte buff and trigger spread shot.

        Args:
            user: PELOTARI unit losing the buff
            game: Game instance
            ui: UI instance for animations
        """
        if not hasattr(user, 'riposte_buff_active') or not user.riposte_buff_active:
            return  # No buff to knock off

        # Remove buff
        user.riposte_buff_active = False
        user.attack_range_bonus = 0
        user.riposte_turns_without_buff = 0

        message_log.add_message(
            f"{user.get_display_name()}'s Riposte converts to spread shot!",
            MessageType.ABILITY,
            player=user.player
        )

        # Trigger spread shot
        self._execute_spread_shot(user, game, ui)

    def _execute_spread_shot(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """
        Execute the Riposte spread shot (6 balls, 120° cone, 4 damage each).

        Args:
            user: PELOTARI unit
            game: Game instance
            ui: UI instance
        """
        from .physics import calculate_spread_shot_trajectories

        # Get toggle mode
        ricochet_mode = getattr(user, 'pelotari_ricochet_mode', True)

        # Calculate spread shot trajectories (120° cone, 6 balls)
        # Direction: away from user's current facing or outward from center
        trajectories = calculate_spread_shot_trajectories(
            start_pos=(user.y, user.x),
            cone_angle=120,
            ball_count=6,
            ricochet_mode=ricochet_mode,
            game=game
        )

        # Execute each ball trajectory
        for trajectory in trajectories:
            self._execute_ball_trajectory(trajectory, damage=4, user=user, game=game, ui=ui)

        logger.debug(f"Riposte spread shot executed: {len(trajectories)} balls")

    def _execute_ball_trajectory(self, trajectory: list, damage: int, user: 'Unit',
                                  game: 'Game', ui=None) -> None:
        """
        Execute a single ball trajectory and apply damage.

        Args:
            trajectory: List of (y, x) positions
            damage: Damage per hit
            user: Source unit
            game: Game instance
            ui: UI instance
        """
        # Check each position in trajectory for units
        for pos in trajectory:
            target = game.get_unit_at(pos[0], pos[1])
            if target and target.player != user.player and target.is_alive():
                # Deal damage
                actual_damage = target.deal_damage(damage)
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=target.get_display_name(),
                    damage=actual_damage,
                    ability="Riposte Spread Shot",
                    attacker_player=user.player,
                    target_player=target.player
                )

                # Ball disappears after hitting unit
                break

        # TODO: Add animation for ball trajectory


class Poach(ActiveSkill):
    """
    Active skill for PELOTARI.
    Knocks buff off enemy, creating steal-able buff ball projectile.
    """

    def __init__(self):
        super().__init__(
            name="Poach",
            key="1",
            description="Knock buff off enemy. Buff becomes steal-able projectile. Random if multiple buffs.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=4
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None,
                game: Optional['Game'] = None) -> bool:
        """Check if Poach can be used."""
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Get effective range (may be boosted by Riposte)
        effective_range = self.range
        if hasattr(user, 'riposte_buff_active') and user.riposte_buff_active:
            effective_range += 2

        # Check range from current or planned position
        source_y, source_x = (user.move_target if user.move_target else (user.y, user.x))
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > effective_range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        # Target must be enemy unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player or not target.is_alive():
            return False

        # Target must have at least one buff
        # TODO: Implement buff detection system
        # For now, assume target has buffs if they have any status effects
        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None,
            game: Optional['Game'] = None) -> bool:
        """Queue Poach skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown

        message_log.add_message(
            f"{user.get_display_name()} prepares to Poach",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Poach skill."""
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False

        message_log.add_message(
            f"{user.get_display_name()} uses Poach on {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player
        )

        # Check if target is enemy PELOTARI with Riposte buff
        if hasattr(target, 'riposte_buff_active') and target.riposte_buff_active:
            # Special case: PELOTARI buff converts to spread shot
            message_log.add_message(
                f"{target.get_display_name()}'s Riposte cannot be stolen!",
                MessageType.ABILITY,
                player=target.player
            )
            # Trigger spread shot at target's position
            if hasattr(target.passive_skill, 'knock_off_buff'):
                target.passive_skill.knock_off_buff(target, game, ui)
            return True

        # TODO: Implement buff detection and removal
        # For now, simulate knocking off a generic buff
        buff_knocked_off = self._knock_off_random_buff(target, game)

        if not buff_knocked_off:
            message_log.add_message(
                f"{target.get_display_name()} has no buffs to steal!",
                MessageType.WARNING,
                player=user.player
            )
            return False

        # Create buff ball projectile
        self._create_buff_ball(
            start_pos=target_pos,
            buff_type=buff_knocked_off,
            source_player=user.player,
            game=game,
            ui=ui
        )

        return True

    def _knock_off_random_buff(self, target: 'Unit', game: 'Game') -> Optional[str]:
        """
        Knock off a random buff from target.

        Returns:
            str: Name of buff knocked off, or None if no buffs
        """
        # TODO: Implement proper buff system
        # For now, return a placeholder
        available_buffs = []

        # Check for common buffs
        if hasattr(target, 'ossify_active') and target.ossify_active:
            available_buffs.append('ossify')
        if hasattr(target, 'valuation_oracle_buff') and target.valuation_oracle_buff:
            available_buffs.append('valuation_oracle')
        # Add more buff checks here

        if not available_buffs:
            return None

        # Pick random buff
        buff_to_remove = random.choice(available_buffs)

        # Remove the buff
        if buff_to_remove == 'ossify':
            target.ossify_active = False
            target.defense_bonus = 0
            target.move_range_bonus = 0
        elif buff_to_remove == 'valuation_oracle':
            target.valuation_oracle_buff = False
            target.defense_bonus = 0
            target.attack_range_bonus = 0

        return buff_to_remove

    def _create_buff_ball(self, start_pos: tuple, buff_type: str, source_player: int,
                          game: 'Game', ui=None) -> None:
        """
        Create buff ball projectile that allies can catch.

        Args:
            start_pos: Starting position (y, x)
            buff_type: Type of buff stolen
            source_player: Player who used Poach
            game: Game instance
            ui: UI instance
        """
        from .physics import calculate_buff_ball_trajectory

        # Get PELOTARI toggle mode
        # TODO: Get this from the actual user unit
        ricochet_mode = True  # Default

        # Calculate trajectory
        trajectory = calculate_buff_ball_trajectory(
            start_pos=start_pos,
            ricochet_mode=ricochet_mode,
            game=game
        )

        # Check trajectory for ally interception
        for pos in trajectory:
            ally = game.get_unit_at(pos[0], pos[1])
            if ally and ally.player == source_player and ally.is_alive():
                # Ally catches buff
                self._apply_buff(ally, buff_type, game)
                message_log.add_message(
                    f"{ally.get_display_name()} catches the {buff_type} buff!",
                    MessageType.ABILITY,
                    player=source_player
                )
                break

        # TODO: Add animation for buff ball trajectory


    def _apply_buff(self, target: 'Unit', buff_type: str, game: 'Game') -> None:
        """Apply stolen buff to ally."""
        # TODO: Implement proper buff application
        if buff_type == 'ossify':
            target.ossify_active = True
            target.defense_bonus = 2
        elif buff_type == 'valuation_oracle':
            target.valuation_oracle_buff = True
            target.defense_bonus = 1
            target.attack_range_bonus = 1


class ResonantBackhand(ActiveSkill):
    """
    Active skill for PELOTARI.
    Counter stance that reflects attacks/skills back as ball projectiles.
    """

    def __init__(self):
        super().__init__(
            name="Resonant Backhand",
            key="2",
            description="Counter stance. Reflects enemy attacks/skills back as ball projectiles.",
            target_type=TargetType.SELF,
            cooldown=4,
            range_=0
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None,
                game: Optional['Game'] = None) -> bool:
        """Check if Resonant Backhand can be used."""
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False

        # Cannot use if trapped
        if hasattr(user, 'trapped_by') and user.trapped_by is not None:
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None,
            game: Optional['Game'] = None) -> bool:
        """Activate Resonant Backhand counter stance."""
        if not self.can_use(user, target_pos, game):
            return False

        # Set counter stance flag
        user.resonant_backhand_active = True
        user.skill_target = (user.y, user.x)
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown

        message_log.add_message(
            f"{user.get_display_name()} readies Resonant Backhand",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute Resonant Backhand (sets up counter for the turn).
        Actual reflection happens when attacked.
        """
        # Stance is already active, just confirm
        user.resonant_backhand_active = True
        logger.debug(f"{user.get_display_name()} Resonant Backhand stance active")
        return True

    def trigger_counter(self, user: 'Unit', attacker: 'Unit', damage: int,
                        game: 'Game', ui=None) -> bool:
        """
        Triggered when PELOTARI is attacked while counter is active.

        Args:
            user: PELOTARI with counter active
            attacker: Unit that attacked
            damage: Damage from attack
            game: Game instance
            ui: UI instance

        Returns:
            bool: True if counter triggered successfully
        """
        if not hasattr(user, 'resonant_backhand_active') or not user.resonant_backhand_active:
            return False

        message_log.add_message(
            f"{user.get_display_name()} catches and returns the attack!",
            MessageType.ABILITY,
            player=user.player
        )

        # Deactivate counter (only works once per turn)
        user.resonant_backhand_active = False

        # Reflect attack back as ball projectile
        self._reflect_attack(user, attacker, damage, game, ui)

        return True

    def _reflect_attack(self, user: 'Unit', attacker: 'Unit', damage: int,
                        game: 'Game', ui=None) -> None:
        """
        Reflect attack back at attacker as ball projectile.

        Args:
            user: PELOTARI
            attacker: Original attacker
            damage: Damage to reflect
            game: Game instance
            ui: UI instance
        """
        from .physics import calculate_reflection_trajectory

        # Get toggle mode
        ricochet_mode = getattr(user, 'pelotari_ricochet_mode', True)

        # Calculate reflection trajectory
        trajectory = calculate_reflection_trajectory(
            start_pos=(user.y, user.x),
            target_pos=(attacker.y, attacker.x),
            ricochet_mode=ricochet_mode,
            game=game
        )

        # Apply damage to first enemy hit in trajectory
        for pos in trajectory:
            target = game.get_unit_at(pos[0], pos[1])
            if target and target.player != user.player and target.is_alive():
                actual_damage = target.deal_damage(damage)
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=target.get_display_name(),
                    damage=actual_damage,
                    ability="Resonant Backhand",
                    attacker_player=user.player,
                    target_player=target.player
                )
                break

        # TODO: Add animation for reflected ball


class Matador(ActiveSkill):
    """
    Active skill for PELOTARI.
    Massive ball nuke that deals 8 damage and displaces units/furniture.
    The killer shot - finishing blow in jai alai.
    """

    def __init__(self):
        super().__init__(
            name="Matador",
            key="3",
            description="Massive ball nuke. 8 damage + knockback. Launches furniture 3-4 tiles. +4 slam damage.",
            target_type=TargetType.AREA,
            cooldown=6,
            range_=4
        )
        self.base_damage = 8
        self.slam_damage = 4
        self.displacement_distance = 3  # Can be 3-4 tiles

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None,
                game: Optional['Game'] = None) -> bool:
        """Check if Matador can be used."""
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Get effective range (may be boosted by Riposte)
        effective_range = self.range
        if hasattr(user, 'riposte_buff_active') and user.riposte_buff_active:
            effective_range += 2

        # Check range
        source_y, source_x = (user.move_target if user.move_target else (user.y, user.x))
        distance = game.chess_distance(source_y, source_x, target_pos[0], target_pos[1])
        if distance > effective_range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(source_y, source_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None,
            game: Optional['Game'] = None) -> bool:
        """Queue Matador for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown

        message_log.add_message(
            f"{user.get_display_name()} charges Matador!",
            MessageType.ABILITY,
            player=user.player
        )

        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Matador nuke."""
        from .physics import calculate_cannonball_trajectory

        message_log.add_message(
            f"{user.get_display_name()} launches Matador!",
            MessageType.ABILITY,
            player=user.player
        )

        # Get toggle mode
        ricochet_mode = getattr(user, 'pelotari_ricochet_mode', True)

        # Calculate trajectory
        trajectory = calculate_cannonball_trajectory(
            start_pos=(user.y, user.x),
            target_pos=target_pos,
            ricochet_mode=ricochet_mode,
            game=game
        )

        # Execute along trajectory
        for i, pos in enumerate(trajectory):
            # Check for unit hit
            target = game.get_unit_at(pos[0], pos[1])
            if target and target.is_alive():
                self._hit_unit(target, user, game, trajectory, i, ui)
                break

            # Check for furniture hit (ricochet mode only)
            if ricochet_mode and game.map.is_furniture(pos[0], pos[1]):
                self._hit_furniture(pos, user, game, trajectory, i, ui)
                # Ball continues after hitting furniture in ricochet mode
                continue

        # TODO: Add animation for giant cannonball

        return True

    def _hit_unit(self, target: 'Unit', user: 'Unit', game: 'Game',
                  trajectory: list, hit_index: int, ui=None) -> None:
        """
        Handle Matador hitting a unit.

        Args:
            target: Unit that was hit
            user: PELOTARI
            game: Game instance
            trajectory: Full trajectory path
            hit_index: Index in trajectory where hit occurred
            ui: UI instance
        """
        # Deal base damage
        actual_damage = target.deal_damage(self.base_damage)

        # Calculate knockback direction (continue along trajectory)
        if hit_index + 1 < len(trajectory):
            knockback_dir = (
                trajectory[hit_index + 1][0] - trajectory[hit_index][0],
                trajectory[hit_index + 1][1] - trajectory[hit_index][1]
            )
        else:
            # Use direction from previous to current
            knockback_dir = (
                trajectory[hit_index][0] - trajectory[hit_index - 1][0],
                trajectory[hit_index][1] - trajectory[hit_index - 1][1]
            ) if hit_index > 0 else (0, 0)

        # Displace unit
        final_pos = self._displace_unit(target, knockback_dir, self.displacement_distance, game)

        # Check for slam damage
        slam_occurred = False
        if final_pos != (target.y, target.x):
            # Check if slammed into terrain
            check_y = final_pos[0] + knockback_dir[0]
            check_x = final_pos[1] + knockback_dir[1]
            if game.is_valid_position(check_y, check_x):
                if not game.map.is_passable(check_y, check_x):
                    slam_occurred = True
                    slam_dmg = target.deal_damage(self.slam_damage)
                    actual_damage += slam_dmg
                    message_log.add_message(
                        f"{target.get_display_name()} slams into terrain (+{slam_dmg} damage)!",
                        MessageType.ABILITY,
                        player=user.player
                    )

        # Log combat
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=actual_damage,
            ability="Matador" + (" (SLAM)" if slam_occurred else ""),
            attacker_player=user.player,
            target_player=target.player
        )

    def _hit_furniture(self, furniture_pos: tuple, user: 'Unit', game: 'Game',
                       trajectory: list, hit_index: int, ui=None) -> None:
        """
        Handle Matador hitting furniture (launches it).

        Args:
            furniture_pos: Position of furniture
            user: PELOTARI
            game: Game instance
            trajectory: Full trajectory path
            hit_index: Index where furniture was hit
            ui: UI instance
        """
        # Calculate launch direction
        if hit_index + 1 < len(trajectory):
            launch_dir = (
                trajectory[hit_index + 1][0] - trajectory[hit_index][0],
                trajectory[hit_index + 1][1] - trajectory[hit_index][1]
            )
        else:
            launch_dir = (0, 0)

        message_log.add_message(
            f"Furniture launches from {furniture_pos}!",
            MessageType.ABILITY,
            player=user.player
        )

        # Calculate furniture trajectory
        furniture_trajectory = self._calculate_furniture_displacement(
            furniture_pos, launch_dir, self.displacement_distance + 1, game
        )

        # Check for units hit by flying furniture
        for furn_pos in furniture_trajectory[1:]:  # Skip starting position
            unit_hit = game.get_unit_at(furn_pos[0], furn_pos[1])
            if unit_hit and unit_hit.is_alive():
                # Furniture hits unit
                furniture_damage = unit_hit.deal_damage(4)  # 4 damage from flying furniture
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=unit_hit.get_display_name(),
                    damage=furniture_damage,
                    ability="Flying Furniture",
                    attacker_player=user.player,
                    target_player=unit_hit.player
                )

        # Move furniture to final position
        final_furn_pos = furniture_trajectory[-1]
        # TODO: Implement furniture relocation in game engine
        logger.debug(f"Furniture relocated from {furniture_pos} to {final_furn_pos}")

    def _displace_unit(self, unit: 'Unit', direction: tuple, max_distance: int,
                       game: 'Game') -> tuple:
        """
        Displace unit in direction.

        Returns:
            tuple: Final position (y, x)
        """
        current_y, current_x = unit.y, unit.x

        for step in range(max_distance):
            new_y = current_y + direction[0]
            new_x = current_x + direction[1]

            # Check if position is valid and passable
            if not game.is_valid_position(new_y, new_x):
                break
            if not game.map.is_passable(new_y, new_x):
                break
            if game.get_unit_at(new_y, new_x):
                break  # Another unit blocks

            current_y, current_x = new_y, new_x

        # Update unit position
        unit.y, unit.x = current_y, current_x
        return (current_y, current_x)

    def _calculate_furniture_displacement(self, start_pos: tuple, direction: tuple,
                                          max_distance: int, game: 'Game') -> list:
        """
        Calculate furniture displacement path.

        Returns:
            list: Path positions [(y, x), ...]
        """
        path = [start_pos]
        current_y, current_x = start_pos

        for step in range(max_distance):
            new_y = current_y + direction[0]
            new_x = current_x + direction[1]

            # Check if position is valid
            if not game.is_valid_position(new_y, new_x):
                break

            # Furniture can pass through units but stops at impassable terrain
            if not game.map.is_passable(new_y, new_x):
                break

            path.append((new_y, new_x))
            current_y, current_x = new_y, new_x

        return path


# Export skills for plugin registration
PASSIVE_SKILL = Riposte
ACTIVE_SKILLS = [Poach, ResonantBackhand, Matador]
