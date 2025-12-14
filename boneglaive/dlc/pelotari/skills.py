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
from boneglaive.utils.animation_helpers import sleep_with_animation_speed

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Riposte(PassiveSkill):
    """
    Passive skill for PELOTARI.
    Grants +2 defense. When hit by basic attack, fires 4 diagonal balls (2 damage each).
    Goes on 3 turn cooldown after triggering.
    """

    def __init__(self):
        super().__init__(
            name="Riposte",
            key="R",
            description="Grants +2 DEF. When hit by basic attack, fires 4 diagonal balls (2 damage, 1 ricochet). 3 turn CD."
        )
        self.defense_bonus = 2
        self.cooldown_turns = 3
        self.ball_damage = 2
        self.ball_range = 4

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """
        Apply Riposte passive effect.
        Grants +2 defense and handles cooldown refresh.
        """
        if not game:
            return

        # Initialize state if needed
        if not hasattr(user, 'riposte_active'):
            user.riposte_active = True  # Start with buff active
            user.riposte_cooldown = 0
            user.defense_bonus = self.defense_bonus
            logger.debug(f"{user.get_display_name()} starts with Riposte (+{self.defense_bonus} DEF)")

        # Handle cooldown refresh
        if not user.riposte_active and user.riposte_cooldown > 0:
            user.riposte_cooldown -= 1
            if user.riposte_cooldown == 0:
                # Refresh buff
                user.riposte_active = True
                user.defense_bonus = self.defense_bonus
                message_log.add_message(
                    f"{user.get_display_name()}'s Riposte recharges (+{self.defense_bonus} DEF)",
                    MessageType.ABILITY,
                    player=user.player
                )
                logger.debug(f"{user.get_display_name()} Riposte recharged")
        elif user.riposte_active:
            # Ensure defense bonus is applied
            if user.defense_bonus < self.defense_bonus:
                user.defense_bonus = self.defense_bonus

    def trigger_on_hit(self, user: 'Unit', attacker: 'Unit', game: 'Game', ui=None) -> None:
        """
        Trigger Riposte when PELOTARI is hit by basic attack.
        Fires 4 diagonal balls and puts Riposte on cooldown.

        Args:
            user: PELOTARI unit that was hit
            attacker: Unit that attacked
            game: Game instance
            ui: UI instance for animations
        """
        if not hasattr(user, 'riposte_active') or not user.riposte_active:
            return  # Riposte not active

        # Remove DEF bonus and start cooldown
        user.riposte_active = False
        user.defense_bonus = 0
        user.riposte_cooldown = self.cooldown_turns

        message_log.add_message(
            f"{user.get_display_name()}'s Riposte triggers! Diagonal spread!",
            MessageType.ABILITY,
            player=user.player
        )

        # Execute diagonal spread shot
        self._execute_diagonal_spread(user, game, ui)

    def _execute_diagonal_spread(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """
        Execute diagonal spread shot (4 balls: NE, NW, SE, SW).
        Each ball: 2 damage, max 4 range, 1 ricochet.

        Args:
            user: PELOTARI unit
            game: Game instance
            ui: UI instance
        """
        # Diagonal directions: NE, NW, SE, SW
        directions = [(-1, 1), (-1, -1), (1, -1), (1, 1)]

        for direction in directions:
            trajectory = self._calculate_diagonal_trajectory(
                start_pos=(user.y, user.x),
                direction=direction,
                max_range=self.ball_range,
                game=game
            )

            # Animate and execute trajectory
            self._execute_ball_trajectory(trajectory, user=user, game=game, ui=ui)

        logger.debug(f"Riposte diagonal spread executed: 4 balls")

    def _calculate_diagonal_trajectory(self, start_pos: tuple, direction: tuple,
                                       max_range: int, game: 'Game') -> list:
        """
        Calculate diagonal trajectory with ricochet capability.

        Args:
            start_pos: Starting (y, x)
            direction: Direction tuple (dy, dx)
            max_range: Maximum range
            game: Game instance

        Returns:
            List of (y, x) positions
        """
        trajectory = []
        current_y, current_x = start_pos
        dy, dx = direction
        bounced = False

        for step in range(max_range):
            next_y = current_y + dy
            next_x = current_x + dx

            # Check bounds
            if not game.is_valid_position(next_y, next_x):
                # Hit edge - ricochet once
                if not bounced:
                    bounced = True
                    # Reflect off edge
                    if next_y < 0 or next_y >= game.map.height:
                        dy = -dy
                    if next_x < 0 or next_x >= game.map.width:
                        dx = -dx
                    continue
                else:
                    break

            # Check impassable terrain
            if not game.map.is_passable(next_y, next_x):
                # Hit wall - ricochet once
                if not bounced:
                    bounced = True
                    # Simple ricochet: reverse direction
                    dy, dx = -dy, -dx
                    continue
                else:
                    break

            trajectory.append((next_y, next_x))
            current_y, current_x = next_y, next_x

        return trajectory

    def _execute_ball_trajectory(self, trajectory: list, user: 'Unit',
                                  game: 'Game', ui=None) -> None:
        """
        Execute a single ball trajectory with animation and damage.

        Args:
            trajectory: List of (y, x) positions
            user: Source unit
            game: Game instance
            ui: UI instance
        """
        # Animate trajectory
        if ui and hasattr(ui, 'renderer'):
            for pos in trajectory:
                ui.renderer.draw_tile(pos[0], pos[1], 'o', 6)  # Yellow ball
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)

        # Check each position for enemy units
        for pos in trajectory:
            target = game.get_unit_at(pos[0], pos[1])
            if target and target.player != user.player and target.is_alive():
                # Deal damage (respect defense)
                damage_after_defense = max(1, self.ball_damage - target.defense)
                target.hp -= damage_after_defense
                target.hp = max(0, target.hp)

                # Log damage
                message_log.add_combat_message(
                    attacker_name=user.get_display_name(),
                    target_name=target.get_display_name(),
                    damage=damage_after_defense,
                    ability="Riposte",
                    attacker_player=user.player,
                    target_player=target.player
                )

                # Show damage number
                if ui and hasattr(ui, 'renderer'):
                    ui.renderer.draw_tile(target.y - 1, target.x * 2, f"-{damage_after_defense}", 1)
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.15)

                # Ball stops after hitting
                break


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
    Always travels in a straight line to target, ignoring toggle mode.
    Can ricochet up to 2 times if targets are pinned/blocked.
    """

    def __init__(self):
        super().__init__(
            name="Matador",
            key="3",
            description="Massive targeted ball. 8 damage + 3-tile knockback. Ricochets up to 2x off walls/pinned targets. +2 slam damage.",
            target_type=TargetType.AREA,
            cooldown=6,
            range_=6
        )
        self.base_damage = 8
        self.slam_damage = 2
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
        message_log.add_message(
            f"{user.get_display_name()} launches Matador!",
            MessageType.ABILITY,
            player=user.player
        )

        # Charging animation at user position
        if ui and hasattr(ui, 'renderer'):
            charging_frames = ['o', 'O', '@', 'O']
            for frame in charging_frames:
                ui.renderer.draw_tile(user.y, user.x, frame, 6)  # Yellow/gold
                ui.renderer.refresh()
                sleep_with_animation_speed(0.15)

        # Calculate straight-line trajectory to target
        # Matador always goes straight - doesn't use ricochet/phase toggle
        trajectory = self._calculate_straight_trajectory(
            start_pos=(user.y, user.x),
            target_pos=target_pos,
            game=game
        )

        # Execute along trajectory - hit first thing in path
        # We'll animate as we go, stopping animation at collision points
        ball_active = True
        bounce_count = 0
        max_bounces = 2  # Ball can ricochet up to 2 times
        current_trajectory = trajectory

        while ball_active and current_trajectory:
            # Animate only up to the collision point
            collision_index = self._find_collision_index(current_trajectory, user, game)
            animation_trajectory = current_trajectory[:collision_index + 1] if collision_index >= 0 else current_trajectory
            self._animate_cannonball_trajectory(animation_trajectory, user, game, ui)

            for i, pos in enumerate(current_trajectory):
                # Check for unit hit (enemy units only)
                target = game.get_unit_at(pos[0], pos[1])
                if target and target.is_alive() and target.player != user.player:
                    # Try to displace unit - if blocked, ricochet
                    if self._hit_unit(target, user, game, current_trajectory, i, ui, bounce_count > 0):
                        ball_active = False
                        break
                    else:
                        # Unit blocked - ricochet if haven't exceeded max bounces
                        if bounce_count < max_bounces:
                            bounce_count += 1
                            ricochet_trajectory = self._calculate_ricochet(pos, user, game)
                            if ricochet_trajectory:
                                # Animate ricochet sparks
                                if ui and hasattr(ui, 'renderer'):
                                    ricochet_frames = ['/', '\\', '|']
                                    for frame in ricochet_frames:
                                        ui.renderer.draw_tile(pos[0], pos[1], frame, 6)
                                        ui.renderer.refresh()
                                        sleep_with_animation_speed(0.1)

                                # Continue with ricochet trajectory (animation happens at loop start)
                                current_trajectory = ricochet_trajectory
                                break
                        ball_active = False
                        break

                # Check for furniture hit
                if game.map.is_furniture(pos[0], pos[1]):
                    # Try to displace furniture - if blocked, ricochet
                    if self._hit_furniture(pos, user, game, current_trajectory, i, ui, bounce_count > 0):
                        ball_active = False
                        break
                    else:
                        # Furniture blocked - ricochet if haven't exceeded max bounces
                        if bounce_count < max_bounces:
                            bounce_count += 1
                            ricochet_trajectory = self._calculate_ricochet(pos, user, game)
                            if ricochet_trajectory:
                                # Animate ricochet sparks
                                if ui and hasattr(ui, 'renderer'):
                                    ricochet_frames = ['/', '\\', '|']
                                    for frame in ricochet_frames:
                                        ui.renderer.draw_tile(pos[0], pos[1], frame, 6)
                                        ui.renderer.refresh()
                                        sleep_with_animation_speed(0.1)

                                # Continue with ricochet trajectory (animation happens at loop start)
                                current_trajectory = ricochet_trajectory
                                break
                        ball_active = False
                        break

                # Check for impassable terrain (walls) - ricochet off them
                if not game.map.is_passable(pos[0], pos[1]):
                    if bounce_count < max_bounces:
                        bounce_count += 1
                        ricochet_trajectory = self._calculate_ricochet(pos, user, game)
                        if ricochet_trajectory:
                            # Animate ricochet sparks
                            if ui and hasattr(ui, 'renderer'):
                                ricochet_frames = ['/', '\\', '|']
                                for frame in ricochet_frames:
                                    # Draw ricochet at last valid position before wall
                                    ricochet_y, ricochet_x = current_trajectory[i-1] if i > 0 else pos
                                    ui.renderer.draw_tile(ricochet_y, ricochet_x, frame, 6)
                                    ui.renderer.refresh()
                                    sleep_with_animation_speed(0.1)

                            # Continue with ricochet trajectory (animation happens at loop start)
                            current_trajectory = ricochet_trajectory
                            break
                    ball_active = False
                    break
            else:
                # Reached end of trajectory (map edge) - try to ricochet
                if bounce_count < max_bounces and len(current_trajectory) > 0:
                    last_pos = current_trajectory[-1]
                    bounce_count += 1
                    ricochet_trajectory = self._calculate_edge_ricochet(last_pos, user, game)
                    if ricochet_trajectory:
                        # Animate ricochet sparks
                        if ui and hasattr(ui, 'renderer'):
                            ricochet_frames = ['/', '\\', '|']
                            for frame in ricochet_frames:
                                ui.renderer.draw_tile(last_pos[0], last_pos[1], frame, 6)
                                ui.renderer.refresh()
                                sleep_with_animation_speed(0.1)

                        # Continue with ricochet trajectory (animation happens at loop start)
                        current_trajectory = ricochet_trajectory
                    else:
                        ball_active = False
                else:
                    ball_active = False

        return True

    def _find_collision_index(self, trajectory: list, user: 'Unit', game: 'Game') -> int:
        """
        Find the first collision point in a trajectory.

        Args:
            trajectory: List of (y, x) positions
            user: PELOTARI unit
            game: Game instance

        Returns:
            int: Index of first collision, or -1 if no collision
        """
        for i, pos in enumerate(trajectory):
            # Check for enemy unit
            target = game.get_unit_at(pos[0], pos[1])
            if target and target.is_alive() and target.player != user.player:
                return i

            # Check for furniture
            if game.map.is_furniture(pos[0], pos[1]):
                return i

            # Check for impassable terrain
            if not game.map.is_passable(pos[0], pos[1]):
                return i - 1 if i > 0 else 0  # Stop before the wall

        return -1  # No collision found

    def _calculate_straight_trajectory(self, start_pos: tuple, target_pos: tuple,
                                       game: 'Game') -> list:
        """
        Calculate straight-line trajectory from start to target and beyond to map edge.

        Args:
            start_pos: Starting position (y, x)
            target_pos: Target position (y, x)
            game: Game instance

        Returns:
            List of (y, x) positions along straight path
        """
        # Calculate direction vector
        dy = target_pos[0] - start_pos[0]
        dx = target_pos[1] - start_pos[1]

        # Normalize to unit direction
        if dy != 0:
            dy = dy // abs(dy)
        if dx != 0:
            dx = dx // abs(dx)

        # Build trajectory from start to map edge in that direction
        trajectory = []
        current_y, current_x = start_pos

        # Travel up to 50 tiles (more than any map dimension)
        for step in range(50):
            next_y = current_y + dy
            next_x = current_x + dx

            # Check if we've hit map edge
            if not game.is_valid_position(next_y, next_x):
                break

            trajectory.append((next_y, next_x))
            current_y, current_x = next_y, next_x

        return trajectory

    def _calculate_edge_ricochet(self, last_pos: tuple, user: 'Unit', game: 'Game') -> list:
        """
        Calculate ricochet trajectory after hitting map edge.

        Args:
            last_pos: Last valid position before hitting edge
            user: PELOTARI unit
            game: Game instance

        Returns:
            List of (y, x) positions for ricochet trajectory
        """
        # Calculate incoming direction
        incoming_dir = (
            last_pos[0] - user.y,
            last_pos[1] - user.x
        )

        # Normalize
        if incoming_dir[0] != 0:
            incoming_dir = (incoming_dir[0] // abs(incoming_dir[0]), incoming_dir[1])
        if incoming_dir[1] != 0:
            incoming_dir = (incoming_dir[0], incoming_dir[1] // abs(incoming_dir[1]))

        # Determine which edge was hit and calculate reflection
        reflection = list(incoming_dir)

        # Check if we're at or near top/bottom edge
        if last_pos[0] == 0 or last_pos[0] == game.map.height - 1:
            # Hit top or bottom edge - flip vertical component
            reflection[0] = -reflection[0]

        # Check if we're at or near left/right edge
        if last_pos[1] == 0 or last_pos[1] == game.map.width - 1:
            # Hit left or right edge - flip horizontal component
            reflection[1] = -reflection[1]

        # Build trajectory in reflection direction
        trajectory = []
        current_pos = last_pos
        max_range = 6  # Ricochet travels up to 6 tiles

        for step in range(max_range):
            next_y = current_pos[0] + reflection[0]
            next_x = current_pos[1] + reflection[1]

            # Check bounds
            if not game.is_valid_position(next_y, next_x):
                break

            trajectory.append((next_y, next_x))
            current_pos = (next_y, next_x)

        return trajectory

    def _calculate_ricochet(self, impact_pos: tuple, user: 'Unit', game: 'Game') -> list:
        """
        Calculate ricochet trajectory after hitting blocked target.

        Args:
            impact_pos: Position where ball hit blocked target
            user: PELOTARI unit
            game: Game instance

        Returns:
            List of (y, x) positions for ricochet trajectory, or empty list if no valid ricochet
        """
        from .physics import calculate_bounce, calculate_surface_normal

        # Calculate incoming direction
        incoming_dir = (
            impact_pos[0] - user.y,
            impact_pos[1] - user.x
        )

        # Normalize
        if incoming_dir[0] != 0:
            incoming_dir = (incoming_dir[0] // abs(incoming_dir[0]), incoming_dir[1])
        if incoming_dir[1] != 0:
            incoming_dir = (incoming_dir[0], incoming_dir[1] // abs(incoming_dir[1]))

        # Calculate surface normal at impact
        normal = calculate_surface_normal(impact_pos, game)
        if not normal:
            return []

        # Calculate reflection direction
        dot_product = incoming_dir[0] * normal[0] + incoming_dir[1] * normal[1]
        reflection = (
            incoming_dir[0] - 2 * dot_product * normal[0],
            incoming_dir[1] - 2 * dot_product * normal[1]
        )

        # Normalize reflection
        if reflection[0] != 0:
            reflection = (reflection[0] // abs(reflection[0]), reflection[1])
        if reflection[1] != 0:
            reflection = (reflection[0], reflection[1] // abs(reflection[1]))

        # Build trajectory in reflection direction
        trajectory = []
        current_pos = impact_pos
        max_range = 6  # Ricochet travels up to 6 tiles

        for step in range(max_range):
            next_y = current_pos[0] + reflection[0]
            next_x = current_pos[1] + reflection[1]

            # Check bounds
            if not game.is_valid_position(next_y, next_x):
                break

            # Stop at impassable terrain
            if not game.map.is_passable(next_y, next_x):
                break

            trajectory.append((next_y, next_x))
            current_pos = (next_y, next_x)

        return trajectory

    def _hit_unit(self, target: 'Unit', user: 'Unit', game: 'Game',
                  trajectory: list, hit_index: int, ui=None, bounced: bool = False) -> bool:
        """
        Handle Matador hitting a unit.

        Args:
            target: Unit that was hit
            user: PELOTARI
            game: Game instance
            trajectory: Full trajectory path
            hit_index: Index in trajectory where hit occurred
            ui: UI instance
            bounced: Whether ball has already bounced

        Returns:
            bool: True if hit was successful, False if unit blocked and ball should ricochet
        """
        # Store original position for animation
        original_pos = (target.y, target.x)

        # Show impact animation
        self._animate_impact(target.y, target.x, ui, slam=False)

        # Deal base damage (respecting defense)
        damage_after_defense = max(1, self.base_damage - target.defense)
        target.hp -= damage_after_defense
        target.hp = max(0, target.hp)
        actual_damage = damage_after_defense

        # Show damage number
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{actual_damage}"
            for flash in range(3):
                ui.renderer.draw_tile(target.y - 1, target.x * 2, damage_text, 1)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)

        # Check if target died from initial hit
        if not target.is_alive():
            message_log.add_combat_message(
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name(),
                damage=actual_damage,
                ability="Matador",
                attacker_player=user.player,
                target_player=target.player
            )
            return True  # Hit successful - unit died

        # Calculate knockback direction: FROM user TO target (direction ball was traveling)
        knockback_dir = (
            target.y - user.y,
            target.x - user.x
        )

        # Normalize to unit vector (-1, 0, 1 for each component)
        if knockback_dir[0] != 0:
            knockback_dir = (knockback_dir[0] // abs(knockback_dir[0]), knockback_dir[1])
        if knockback_dir[1] != 0:
            knockback_dir = (knockback_dir[0], knockback_dir[1] // abs(knockback_dir[1]))

        # Try to displace unit
        original_unit_pos = (target.y, target.x)
        final_pos = self._displace_unit(target, knockback_dir, self.displacement_distance, game)

        # Check if unit was actually displaced
        if final_pos == original_unit_pos:
            # Unit couldn't be displaced (blocked immediately) - ball should ricochet
            # Still log the combat damage
            message_log.add_combat_message(
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name(),
                damage=actual_damage,
                ability="Matador (RICOCHET)",
                attacker_player=user.player,
                target_player=target.player
            )

            message_log.add_message(
                f"{target.get_display_name()} is pinned! Ball ricochets!",
                MessageType.ABILITY,
                player=user.player
            )

            # Check if target died from damage even though pinned
            if not target.is_alive():
                logger.debug(f"{target.get_display_name()} died from Matador ricochet (total: {actual_damage} damage)")
                return True  # Unit died, don't ricochet

            return False  # Unit blocked - ricochet

        # Animate knockback
        if ui and hasattr(ui, 'renderer') and final_pos != original_unit_pos:
            # Show unit being pushed back
            message_log.add_message(
                f"{target.get_display_name()} is knocked back!",
                MessageType.ABILITY,
                player=user.player
            )
            sleep_with_animation_speed(0.2)

        # Check for slam damage
        slam_occurred = False
        slam_dmg = 0
        if final_pos != original_pos:
            # Check if slammed into terrain
            check_y = final_pos[0] + knockback_dir[0]
            check_x = final_pos[1] + knockback_dir[1]
            if game.is_valid_position(check_y, check_x):
                if not game.map.is_passable(check_y, check_x):
                    slam_occurred = True
                    # Apply slam damage (respecting defense)
                    slam_damage_after_defense = max(1, self.slam_damage - target.defense)
                    target.hp -= slam_damage_after_defense
                    target.hp = max(0, target.hp)
                    slam_dmg = slam_damage_after_defense
                    actual_damage += slam_dmg

                    # Show slam impact animation
                    self._animate_impact(final_pos[0], final_pos[1], ui, slam=True)

                    message_log.add_message(
                        f"{target.get_display_name()} slams into terrain (+{slam_dmg} damage)!",
                        MessageType.ABILITY,
                        player=user.player
                    )

                    # Show slam damage number
                    if ui and hasattr(ui, 'renderer'):
                        slam_text = f"-{slam_dmg}!"
                        for flash in range(3):
                            ui.renderer.draw_tile(final_pos[0] - 1, final_pos[1] * 2, slam_text, 1)
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)

        # Log combat
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=actual_damage,
            ability="Matador" + (" (SLAM)" if slam_occurred else ""),
            attacker_player=user.player,
            target_player=target.player
        )

        # Check if target died
        if not target.is_alive():
            logger.debug(f"{target.get_display_name()} died from Matador (total: {actual_damage} damage)")

        return True  # Hit successful - unit took damage and was displaced

    def _hit_furniture(self, furniture_pos: tuple, user: 'Unit', game: 'Game',
                       trajectory: list, hit_index: int, ui=None, bounced: bool = False) -> bool:
        """
        Handle Matador hitting furniture (launches it).

        Args:
            furniture_pos: Position of furniture
            user: PELOTARI
            game: Game instance
            trajectory: Full trajectory path
            hit_index: Index where furniture was hit
            ui: UI instance
            bounced: Whether ball has already bounced

        Returns:
            bool: True if hit was successful, False if furniture blocked and ball should ricochet
        """
        from boneglaive.game.map import TerrainType

        # Get furniture type before moving it
        furniture_type = game.map.get_terrain_at(furniture_pos[0], furniture_pos[1])

        # Calculate launch direction: FROM user TO furniture (direction ball was traveling)
        launch_dir = (
            furniture_pos[0] - user.y,
            furniture_pos[1] - user.x
        )

        # Normalize to unit vector
        if launch_dir[0] != 0:
            launch_dir = (launch_dir[0] // abs(launch_dir[0]), launch_dir[1])
        if launch_dir[1] != 0:
            launch_dir = (launch_dir[0], launch_dir[1] // abs(launch_dir[1]))

        message_log.add_message(
            f"Furniture launches from ({furniture_pos[0]}, {furniture_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )

        # Calculate furniture trajectory (3-4 tiles)
        furniture_trajectory = self._calculate_furniture_displacement(
            furniture_pos, launch_dir, self.displacement_distance + 1, game
        )

        # Check if furniture can actually be displaced
        if len(furniture_trajectory) <= 1:
            # Furniture blocked immediately - ball should ricochet
            message_log.add_message(
                f"Furniture is pinned! Ball ricochets!",
                MessageType.ABILITY,
                player=user.player
            )
            return False

        # Animate furniture tumbling through the air
        if ui and hasattr(ui, 'renderer'):
            for furn_pos in furniture_trajectory[1:]:  # Skip starting position
                ui.renderer.draw_tile(furn_pos[0], furn_pos[1], '*', 7)  # White tumbling furniture
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)

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

                # Show damage number
                if ui and hasattr(ui, 'renderer'):
                    damage_text = f"-{furniture_damage}"
                    for flash in range(2):
                        ui.renderer.draw_tile(unit_hit.y - 1, unit_hit.x * 2, damage_text, 7)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)

        # Move furniture to final position
        final_furn_pos = furniture_trajectory[-1]

        # Clear old position
        game.map.set_terrain_at(furniture_pos[0], furniture_pos[1], TerrainType.EMPTY)

        # Place furniture at new position
        game.map.set_terrain_at(final_furn_pos[0], final_furn_pos[1], furniture_type)

        # Transfer cosmic values if DELPHIC_APPRAISER system is in use
        if hasattr(game.map, 'cosmic_values'):
            for player in list(game.map.cosmic_values.keys()):
                if furniture_pos in game.map.cosmic_values[player]:
                    # Transfer the value to new position
                    value = game.map.cosmic_values[player].pop(furniture_pos)
                    game.map.cosmic_values[player][final_furn_pos] = value

        # Show dust cloud on landing
        if ui and hasattr(ui, 'renderer'):
            dust_frames = ['.', ':', '.']
            for frame in dust_frames:
                ui.renderer.draw_tile(final_furn_pos[0], final_furn_pos[1], frame, 7)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.08)

        logger.debug(f"Furniture relocated from {furniture_pos} to {final_furn_pos}")

        return True  # Furniture was successfully displaced

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

    def _animate_cannonball_trajectory(self, trajectory: list, user: 'Unit',
                                       game: 'Game', ui=None) -> None:
        """
        Animate the massive cannonball traveling along its trajectory.

        Args:
            trajectory: List of (y, x) positions the ball travels through
            user: PELOTARI unit
            game: Game instance
            ui: UI instance for rendering
        """
        if not ui or not hasattr(ui, 'renderer'):
            return

        # Get toggle mode for visual style
        ricochet_mode = getattr(user, 'pelotari_ricochet_mode', True)

        # Ball character and color
        ball_char = 'O'  # Massive ball
        trail_char = 'o'  # Smaller trail
        ball_color = 7  # Bright white for ricochet
        trail_color = 7

        # Phase mode: ghostly appearance
        if not ricochet_mode:
            ball_color = 14  # Cyan/ghostly (if available, fallback to 6)
            trail_color = 6

        # Animate ball moving through trajectory
        for i, pos in enumerate(trajectory):
            y, x = pos

            # Draw the massive ball
            ui.renderer.draw_tile(y, x, ball_char, ball_color)
            ui.renderer.refresh()
            sleep_with_animation_speed(0.08)

            # Leave a brief trail
            if i > 0:
                prev_y, prev_x = trajectory[i-1]
                ui.renderer.draw_tile(prev_y, prev_x, trail_char, trail_color)

            ui.renderer.refresh()

            # Clear trail after a moment
            if i > 1:
                old_y, old_x = trajectory[i-2]
                # Restore terrain at old position
                terrain_type = game.map.get_terrain_at(old_y, old_x)
                # Just clear it - the renderer will handle terrain display
                ui.renderer.refresh()

    def _animate_impact(self, y: int, x: int, ui=None, slam: bool = False) -> None:
        """
        Animate explosive impact when ball hits target.

        Args:
            y, x: Impact position
            ui: UI instance for rendering
            slam: If True, show extra dramatic slam effect
        """
        if not ui or not hasattr(ui, 'renderer'):
            return

        # Impact sequence
        if slam:
            # More dramatic slam animation
            impact_frames = ['*', '#', '!', '#', '*', 'X']
            impact_color = 1  # Red for slam
        else:
            # Standard impact
            impact_frames = ['*', '#', '*', 'X']
            impact_color = 7  # White

        # Show impact animation
        for frame in impact_frames:
            ui.renderer.draw_tile(y, x, frame, impact_color)
            ui.renderer.refresh()
            sleep_with_animation_speed(0.12)

        # Brief pause
        sleep_with_animation_speed(0.15)


# Export skills for plugin registration
PASSIVE_SKILL = Riposte
ACTIVE_SKILLS = [Poach, ResonantBackhand, Matador]
