#!/usr/bin/env python3
"""
Skills specific to the GRAYMAN unit type.
This module contains all passive and active abilities for GRAYMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Stasiality(PassiveSkill):
    """Passive skill for GRAYMAN. Immune to status effects and displacement."""

    def __init__(self):
        super().__init__(
            name="Stasiality",
            key="S",
            description="Cannot have stats changed or be displaced. Immune to buffs, debuffs, forced movement, and terrain effects."
        )

    def apply_passive(self, user: 'Unit', game=None, ui=None) -> None:
        """
        Apply Stasiality passive effects.
        Base: Immunity to status effects (handled in Unit.is_immune_to_effects())
        Upgraded: Enemy unit cooldowns don't decrement when adjacent (handled in Unit.tick_cooldowns())
        """
        pass


class DeltaConfigSkill(ActiveSkill):
    """Active skill for GRAYMAN. Teleports to any unoccupied tile on the map."""
    
    def __init__(self):
        super().__init__(
            name="Delta Config",
            key="D",
            description="Teleport to any unoccupied tile on the map.",
            target_type=TargetType.AREA,
            cooldown=6,
            range_=99
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Target position must be valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Target position must be passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        # Target position must be empty (no unit)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # Check if any other unit is already planning to teleport to this position
        # (via Vault, Delta Config, Grae Exchange, or any other teleport skill)
        for other_unit in game.units:
            if (other_unit.is_alive() and other_unit != user):
                # Check for vault targets
                if (hasattr(other_unit, 'vault_target_indicator') and
                    other_unit.vault_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self

        # Don't clear move_target - allow move+skill combos
        # If user moves first, they can reposition before teleporting

        # Set teleport target indicator for UI
        user.teleport_target_indicator = target_pos

        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} energizes and assumes the Delta Configuration to ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Delta Config teleportation skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.game.upgrades import UpgradeManager

        # SAFETY CHECK: Verify target position is still valid and empty
        # (Another unit might have moved there between planning and execution)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            message_log.add_message(
                f"{user.get_display_name()}'s Delta Config failed - target position occupied",
                MessageType.WARNING,
                player=user.player
            )
            # Clear indicators and return failure
            user.teleport_target_indicator = None
            return False

        # Clear the teleport target indicator after execution
        user.teleport_target_indicator = None

        # Store original position for animations
        original_pos = (user.y, user.x)

        # Check if skill is upgraded
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Delta Config")

        # If upgraded, collect adjacent enemies for abduction
        abducted_enemies = []
        if is_upgraded:
            adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dy, dx in adjacent_offsets:
                adj_y = original_pos[0] + dy
                adj_x = original_pos[1] + dx
                if game.is_valid_position(adj_y, adj_x):
                    enemy = game.get_unit_at(adj_y, adj_x)
                    if (enemy and enemy.player != user.player and enemy.is_alive()
                            and not enemy.is_immune_to_effects()):
                        abducted_enemies.append((enemy, dy, dx))

        # Log the skill activation with different message if upgraded
        if is_upgraded and abducted_enemies:
            enemy_names = ", ".join([e[0].get_display_name() for e in abducted_enemies])
            message_log.add_message(
                f"{user.get_display_name()} creates an electromagnetic well, capturing {enemy_names}",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} de-energizes",
                MessageType.ABILITY,
                player=user.player
            )

        # Play animation if UI is available
        # Apply the teleport (atomic position update)
        # Teleport atomically: remove from old position, update coordinates, add to new position
        # This avoids intermediate position checks that would block the teleport
        final_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if final_unit is not None and final_unit != user:
            # Target occupied (should have been caught by can_use, but check anyway)
            logger.error(f"TELEPORT BLOCKED: {user.get_display_name()}'s Delta Config to {target_pos} blocked - position occupied by {final_unit.get_display_name()}")
            message_log.add_message(
                f"{user.get_display_name()}'s Delta Config blocked - position occupied!",
                MessageType.WARNING,
                player=user.player
            )
            return False

        # Teleport atomically: remove from old position, update coordinates, add to new position
        old_y, old_x = user.y, user.x
        if (old_y, old_x) in game.unit_grid:
            del game.unit_grid[(old_y, old_x)]

        # Set private attributes directly (bypass property setters)
        user._y = target_pos[0]
        user._x = target_pos[1]

        # Add to new position in grid
        game.unit_grid[(target_pos[0], target_pos[1])] = user

        # Trigger trap checks if unit was trapped or is a foreman
        if hasattr(user, 'trapped_by') and user.trapped_by is not None:
            game._check_position_change_trap_release(user, old_y, old_x)
        if user.type == UnitType.MANDIBLE_FOREMAN:
            game._check_position_change_trap_release(user, old_y, old_x)

        # MOVE ABDUCTED ENEMIES TO DESTINATION (both with and without UI)
        if is_upgraded and abducted_enemies:
            adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            # Move each abducted enemy to their new position around the destination
            for enemy, rel_dy, rel_dx in abducted_enemies:
                # Try to maintain relative position
                dest_y = target_pos[0] + rel_dy
                dest_x = target_pos[1] + rel_dx

                # Check if target position is valid and empty
                if (game.is_valid_position(dest_y, dest_x) and
                    game.map.is_passable(dest_y, dest_x) and
                    game.get_unit_at(dest_y, dest_x) is None):
                    # Atomically move enemy: remove from old grid position, update coords, add to new grid position
                    old_enemy_y, old_enemy_x = enemy.y, enemy.x
                    if (old_enemy_y, old_enemy_x) in game.unit_grid:
                        del game.unit_grid[(old_enemy_y, old_enemy_x)]

                    # Set private attributes directly (bypass property setters to avoid double grid updates)
                    enemy._y = dest_y
                    enemy._x = dest_x

                    # Add to new position in grid
                    game.unit_grid[(dest_y, dest_x)] = enemy

                    # Mark enemy as abducted for graphical teleport animation
                    enemy.abducted_by_delta_config = True

                    # Trigger trap checks if enemy was trapped or is a foreman
                    if hasattr(enemy, 'trapped_by') and enemy.trapped_by is not None:
                        game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)
                    if enemy.type == UnitType.MANDIBLE_FOREMAN:
                        game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)
                else:
                    # Fallback: find any valid adjacent position around destination
                    placed = False
                    for alt_dy, alt_dx in adjacent_offsets:
                        alt_y = target_pos[0] + alt_dy
                        alt_x = target_pos[1] + alt_dx
                        if (game.is_valid_position(alt_y, alt_x) and
                            game.map.is_passable(alt_y, alt_x) and
                            game.get_unit_at(alt_y, alt_x) is None):
                            # Atomically move enemy to fallback position
                            old_enemy_y, old_enemy_x = enemy.y, enemy.x
                            if (old_enemy_y, old_enemy_x) in game.unit_grid:
                                del game.unit_grid[(old_enemy_y, old_enemy_x)]

                            # Set private attributes directly (bypass property setters)
                            enemy._y = alt_y
                            enemy._x = alt_x

                            # Add to new position in grid
                            game.unit_grid[(alt_y, alt_x)] = enemy

                            # Mark enemy as abducted for graphical teleport animation
                            enemy.abducted_by_delta_config = True

                            # Trigger trap checks if enemy was trapped or is a foreman
                            if hasattr(enemy, 'trapped_by') and enemy.trapped_by is not None:
                                game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)
                            if enemy.type == UnitType.MANDIBLE_FOREMAN:
                                game._check_position_change_trap_release(enemy, old_enemy_y, old_enemy_x)

                            placed = True
                            break

                    # If no position found, enemy stays at original position (well failed to capture fully)
                    # No need to do anything - enemy is already at their original position in the grid

        # Log the completion of teleportation
        if is_upgraded and abducted_enemies:
            message_log.add_message(
                f"The electromagnetic well warps from ({original_pos[0]}, {original_pos[1]}) to ({target_pos[0]}, {target_pos[1]}), releasing its cargo",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} and the distant point at ({original_pos[0]}, {original_pos[1]}) snap to position ({target_pos[0]}, {target_pos[1]})",
                MessageType.ABILITY,
                player=user.player
            )

        return True


class EstrangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Phases a target out of normal spacetime."""
    
    def __init__(self):
        super().__init__(
            name="Estrange",
            key="E",
            description="Fires a beam that phases target out of normal spacetime. Target receives -2 to all actions.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )
        self.damage = 4
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False

        # Check if target is an enemy (not same player)
        if target_unit.player == user.player:
            return False

        # Cannot target untargetable units (e.g., Karrier Rave phasing)
        if target_unit.is_untargetable():
            return False

        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target

        # Check if target is within range from the correct position
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(from_y, from_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])

        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} charges the estrangement beam targeting {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )

        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Estrange skill to phase a target out of normal spacetime."""
        from boneglaive.utils.message_log import message_log, MessageType


        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False

        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} fires an estrangement beam at {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        
        # Apply damage with defense reduction
        effective_defense = target.get_effective_stats()['defense']
        damage = max(1, self.damage - effective_defense)
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Estrange",
            attacker_player=user.player,
            target_player=target.player
        )
        
        
        # Apply estranged effect if not immune
        if not target.is_immune_to_effects():
            target.estranged = True
            target.estranged_duration = 3

            # Check if Estrange is upgraded
            from boneglaive.game.upgrades import UpgradeManager
            is_upgraded = UpgradeManager.is_skill_upgraded(user, "Estrange")

            # If upgraded, reduce target's max HP by 25%
            if is_upgraded:
                # Only apply max HP reduction if not already applied
                if not hasattr(target, 'estranged_original_max_hp'):
                    # Store original max HP for potential cleansing
                    target.estranged_original_max_hp = target.max_hp

                    # Calculate new max HP (75% of original)
                    new_max_hp = int(target.max_hp * 0.75)
                    target.max_hp = new_max_hp

                    # Adjust current HP if it exceeds new max HP
                    if target.hp > new_max_hp:
                        target.hp = new_max_hp

            # Log the effect application - using WARNING type for yellow text
            message_log.add_message(
                f"{target.get_display_name()} is phased out of normal spacetime",
                MessageType.WARNING,
                player=user.player,
                target_name=target.get_display_name()
            )
            
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to Estrange due to Stasiality",
                MessageType.ABILITY,
                player=target.player,  # Use target's player for correct color coding
                target_name=target.get_display_name()
            )
            
        
        # Check if target was defeated and handle death properly
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="estrange", ui=ui)
        
        # Redraw board after animations
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class GraeExchangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Banishes target enemy and replaces them with a GRAYMAN doppelganger."""

    def __init__(self):
        super().__init__(
            name="Græ Exchange",
            key="G",
            description="Banish target enemy unit and replace them with a GRAYMAN doppelganger for 2 turns.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False

        # Check if target is an enemy (not same player)
        if target_unit.player == user.player:
            return False

        # Cannot target untargetable units (e.g., Karrier Rave phasing)
        if target_unit.is_untargetable():
            return False

        # Check if target is immune to banishment (GRAYMAN with Stasiality)
        if target_unit.type == UnitType.GRAYMAN:
            # GRAYMAN units (including doppelgangers) cannot be banished
            is_doppelganger = hasattr(target_unit, 'is_doppelganger') and target_unit.is_doppelganger
            if target_unit.is_immune_to_effects() or is_doppelganger:
                return False

        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target

        # Check if target is within range from the correct position
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check line of sight
        if not game.has_line_of_sight(from_y, from_x, target_pos[0], target_pos[1]):
            return False

        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])

        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()}'s cane gleams as they prepare to replace {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )

        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Græ Exchange skill - banish target enemy and replace with doppelganger."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger

        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            message_log.add_message(
                f"{user.get_display_name()}'s Græ Exchange failed - target not found",
                MessageType.WARNING,
                player=user.player
            )
            return False

        # Check if target is immune to banishment due to Stasiality
        if target.type == UnitType.GRAYMAN:
            # GRAYMAN units (including doppelgangers) are immune to banishment
            is_doppelganger = hasattr(target, 'is_doppelganger') and target.is_doppelganger
            if target.is_immune_to_effects() or is_doppelganger:
                message_log.add_message(
                    f"{target.get_display_name()} is immune to banishment due to Stasiality",
                    MessageType.ABILITY,
                    player=target.player
                )
                # Skill fails but cooldown is still consumed
                self.current_cooldown = self.cooldown
                return True

        # Log the banishment
        message_log.add_message(
            f"{user.get_display_name()} banishes {target.get_display_name()} and summons a doppelgänger in their place",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )

        # Store target position for doppelganger spawning (needed before animation)
        banished_pos = (target.y, target.x)


        # Log banishment message
        message_log.add_message(
            f"{target.get_display_name()} is banished to the void!",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )

        # Mark the unit as banished so they don't award GP
        target.is_banished = True

        # Remove target from game (banishment - temporary)
        if target in game.units:
            game.units.remove(target)
            game._remove_from_unit_grid(target)

        # Create GRAYMAN doppelganger at the banished target's location
        from boneglaive.game.units import Unit
        doppelganger_unit = Unit(user.type, user.player, banished_pos[0], banished_pos[1])
        doppelganger_unit.initialize_skills()
        doppelganger_unit.set_game_reference(game)

        # Set doppelganger properties
        doppelganger_unit.is_doppelganger = True
        doppelganger_unit.doppelganger_duration = 2  # Doppelganger lasts 2 turns
        doppelganger_unit.original_unit = user
        doppelganger_unit.hp = 12
        doppelganger_unit.max_hp = 12
        doppelganger_unit.attack = 4

        # Store the banished unit in the doppelganger so we can return them later
        doppelganger_unit.banished_unit = target

        # Visual identifier
        if hasattr(user, 'greek_id') and user.greek_id:
            doppelganger_unit.greek_id = user.greek_id.lower()

        # Copy upgraded_skills from the original unit to the doppelganger
        if hasattr(user, 'upgraded_skills'):
            doppelganger_unit.upgraded_skills = set(user.upgraded_skills)

        # Add doppelganger to game
        game.units.append(doppelganger_unit)

        # CRITICAL: Add doppelganger to spatial grid so get_unit_at() can find it
        game._update_unit_grid(doppelganger_unit)

        logger.info(f"DOPPELGANGER SPAWNED from banishment: {doppelganger_unit.type.name} at position ({banished_pos[0]}, {banished_pos[1]})")

        # Log doppelganger spawn
        message_log.add_message(
            f"A GRAYMAN doppelganger manifests in {target.get_display_name()}'s place",
            MessageType.ABILITY,
            player=user.player
        )

        # Redraw board to show the result
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)

        return True