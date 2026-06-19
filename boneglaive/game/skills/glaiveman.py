#!/usr/bin/env python3
"""
Skills specific to the GLAIVEMAN unit type.
This module contains all passive and active abilities for GLAIVEMAN units.
"""



from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Autoclave(PassiveSkill):
    """
    Passive skill for GLAIVEMAN.
    When the GLAIVEMAN wretches (is brought to critical health but not killed)
    or takes damage while already at critical health,
    he retaliates with a four-directional, range 3, cross-shaped attack that
    heals him for half of the damage he dealt.
    Can only occur once per game per GLAIVEMAN.
    Only triggers if there is at least one enemy unit in the attack path.
    """
    
    def __init__(self):
        super().__init__(
            name="Autoclave",
            key="A",
            description="When retched or damaged while at critical health, unleashes a cross-shaped attack in four directions (range 3) and heals for half the damage dealt. One-time use. Requires an enemy in range."
        )
        self.activated = False  # Track if this skill has been used
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """
        Apply the Autoclave passive effect.
        This method is kept for backward compatibility and as a fallback check.
        """
        from boneglaive.utils.debug import logger
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        
        # If already activated or no game, skip
        if self.activated or not game:
            return
            
        # Check if the unit is in critical health - one more chance to trigger if missed
        critical_threshold = int(user.max_hp * CRITICAL_HEALTH_PERCENT)
        
        if user.hp <= critical_threshold:
            logger.debug(f"Fallback check for Autoclave in apply_passive for {user.get_display_name()}")
            
            # Try to trigger now via the new system if there are targets
            if hasattr(game, 'try_trigger_autoclave'):
                game.try_trigger_autoclave(user)
            # If game doesn't have the new method (fallback for compatibility), use old logic
            elif self._has_eligible_targets(user, game) and not self.activated:
                logger.debug("Using legacy fallback method to trigger Autoclave")
                self._trigger_autoclave(user, game)
                self.activated = True
        
    def _has_eligible_targets(self, user: 'Unit', game: 'Game') -> bool:
        """Check if there are any eligible targets for Autoclave."""
        from boneglaive.utils.debug import logger
        
        # Define the four directions (up, right, down, left)
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        
        # Check each direction up to range 3
        for direction_idx, (dy, dx) in enumerate(directions):
            direction_name = ["upward", "rightward", "downward", "leftward"][direction_idx]
            logger.debug(f"Checking {direction_name} direction for Autoclave targets")
            
            for distance in range(1, 4):  # Range 1-3
                target_y = user.y + (dy * distance)
                target_x = user.x + (dx * distance)
                
                # Check if position is valid
                if not game.is_valid_position(target_y, target_x):
                    logger.debug(f"Position ({target_y},{target_x}) is out of bounds, skipping")
                    continue
                
                # Check if terrain is passable - stop checking this direction if we hit terrain
                if not game.map.is_passable(target_y, target_x):
                    logger.debug(f"Terrain at ({target_y},{target_x}) blocks Autoclave path, stopping this direction")
                    break
                    
                # Check if there's an enemy unit at this position
                target = game.get_unit_at(target_y, target_x)
                if target and target.player != user.player:
                    logger.debug(f"Found eligible Autoclave target: {target.get_display_name()} at ({target_y},{target_x})")
                    return True  # Found at least one eligible target
                
                logger.debug(f"No target at ({target_y},{target_x}), continuing search")
                    
        logger.debug("No eligible targets found for Autoclave in any direction")
        return False  # No eligible targets found
            
    def _trigger_autoclave(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """Execute the Autoclave retaliation effect."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger

        logger.debug(f"EXECUTING AUTOCLAVE for {user.get_display_name()}")

        message_log.add_message(
            f"{user.get_display_name()}'s Autoclave activates",
            MessageType.ABILITY,
            player=user.player
        )

        # Use passed UI parameter if provided, otherwise check the game for one
        if ui is None:
            # Get animation component from the game UI if available
            # We need to check if the game has a ui attribute since some tests may not have it
            ui = getattr(game, 'ui', None)

        # The GameStateAdapter automatically detects passive skill activation and queues
        # the animation via the event system (game_state.py:723-741); nothing to trigger here.

        # Define the four directions (up, right, down, left)
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]

        # Track total damage dealt for healing
        total_damage = 0
        affected_units = []

        
        # Check each direction up to range 3 and store valid target info
        targets_by_direction = {}
        for direction_idx, (dy, dx) in enumerate(directions):
            targets_in_direction = []
            
            for distance in range(1, 4):  # Range 1-3
                target_y = user.y + (dy * distance)
                target_x = user.x + (dx * distance)
                
                # Check if position is valid
                if not game.is_valid_position(target_y, target_x):
                    continue
                
                # Check if terrain is passable - stop the beam if it hits impassable terrain
                if not game.map.is_passable(target_y, target_x):
                    # Add position for animation but don't continue past this point
                    targets_in_direction.append((target_y, target_x))
                    break
                    
                # Mark this position for animation
                targets_in_direction.append((target_y, target_x))
                
                # Check if there's a unit at this position
                target = game.get_unit_at(target_y, target_x)
                if target and target.player != user.player:
                    # Calculate damage, accounting for defense
                    damage = max(1, 8 - target.defense)
                    
                    # Apply damage to target
                    previous_hp = target.hp
                    target.hp = max(0, target.hp - damage)
                    
                    # Track total damage for healing
                    total_damage += damage
                    affected_units.append(target)
                    
                    # Log the attack
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=target.get_display_name(),
                        damage=damage,  # Already using the calculated damage value
                        ability="Autoclave",
                        attacker_player=user.player,
                        target_player=target.player
                    )
                    
                    # Graphical version handles damage display through animation system
                    
                    # Check if target was defeated and handle death properly
                    if target.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(target, user, cause="autoclave", ui=ui)
            
            # Store targets for animation
            if targets_in_direction:
                targets_by_direction[direction_idx] = targets_in_direction

        
        # Calculate healing (half of total damage dealt)
        healing = total_damage // 2
        if healing > 0:
            # Apply healing using universal heal method
            actual_healing = user.heal(healing, "Autoclave life essence")
            healing = actual_healing  # Update healing variable for display purposes

            
            # Log the healing
            message_log.add_message(
                f"{user.get_display_name()} absorbs life essence, healing for {healing} HP",
                MessageType.ABILITY,
                player=user.player
            )
            

        # Check for Autoclave upgrade - queue glaive sweep for next critical health trigger
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Autoclave")
        if is_upgraded:
            # Instead of executing immediately, queue the sweep for next critical health trigger
            user.glaive_sweep_queued = True
            message_log.add_message(
                f"{user.get_display_name()}'s glaive is prepared for another counter attack",
                MessageType.ABILITY,
                player=user.player
            )

    def _execute_glaive_sweep(self, user: 'Unit', game: 'Game', ui=None) -> None:
        """Execute the queued glaive sweep counter attack."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger

        user.last_executed_glaive_sweep = True

        logger.debug(f"EXECUTING GLAIVE SWEEP for {user.get_display_name()}")

        message_log.add_message(
            f"{user.get_display_name()}'s glaive swings in a wide arc",
            MessageType.ABILITY,
            player=user.player
        )

        # Detect if running in graphical mode
        is_graphical = hasattr(ui, '__class__') and ui.__class__.__name__ == 'GraphicalUIAdapter'

        # Hit all 8 adjacent tiles
        adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        melee_damage = 5  # Melee counter attack damage

        # Note: Graphical mode animation is handled by renderer detection system in renderer.py
        # The renderer detects the glaive_sweep_queued flag via game_state.py state capture
        # and triggers the GlaiveSweepAnimation when the passive executes during an attack.
        # See: boneglaive/graphical/game_state.py (line ~724) and renderer.py (line ~2532)


        # Calculate damage for all adjacent enemies
        for dy, dx in adjacent_offsets:
            adj_y, adj_x = user.y + dy, user.x + dx
            if game.is_valid_position(adj_y, adj_x):
                adjacent_target = game.get_unit_at(adj_y, adj_x)
                if adjacent_target and adjacent_target.player != user.player and adjacent_target.is_alive():
                    # Calculate damage with defense
                    defense_reduced = max(1, melee_damage - adjacent_target.defense)
                    adjacent_target.hp -= defense_reduced

                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=adjacent_target.get_display_name(),
                        damage=defense_reduced,
                        ability="Glaive Sweep",
                        attacker_player=user.player,
                        target_player=adjacent_target.player
                    )


                    # Check for death
                    if adjacent_target.hp <= 0:
                        game.handle_unit_death(adjacent_target, user, cause="glaive_sweep", ui=ui)

        # Clear the queued flag after execution
        user.glaive_sweep_queued = False


class PrySkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Pry forces an enemy unit straight up into the air where they slam into 
    the ceiling or skybox, breaking loose debris that crashes down with them.
    The primary target takes damage and has their movement reduced, while
    adjacent enemy units also take splash damage from falling debris.
    """
    
    def __init__(self):
        super().__init__(
            name="Pry",
            key="P",
            description="Pries an enemy up to range 1, damaging them and adjacent enemies with falling debris. Reduces target's movement by 1.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=1
        )
        self.primary_damage = 6  # Primary target damage
        self.splash_damage = 3   # Splash damage to adjacent units
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Pry can be used on the target."""
        # First check basic cooldown
        if not super().can_use(user, target_pos, game):
            return False
            
        # Need game and target position to validate
        if not game or not target_pos:
            return False
            
        # Check if there's an enemy unit at target position
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player:
            return False

        # Cannot target untargetable units (e.g., Karrier Rave phasing)
        if target.is_untargetable():
            return False

        # Check if target is within range from the correct position
        # (either current position or planned move position)
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target

        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """
        Queue up the Pry skill for execution at the end of the turn.
        This now works similarly to move and attack actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Validate skill use conditions
        if not self.can_use(user, target_pos, game):
            return False
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Set the skill target
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order (assumes the Game instance is passed)
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Set cooldown - done immediately when queuing up the action
        self.current_cooldown = self.cooldown
        
        # Log that the skill has been queued (this was already correctly implemented)
        message_log.add_message(
            f"{user.get_display_name()} readies to pry {target.get_display_name()} skyward",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """
        Execute the Pry skill during the turn resolution phase.
        This is called by the game engine when processing actions.
        """
        from boneglaive.utils.message_log import message_log, MessageType

        
        # Get target unit (might have moved)
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player:
            # Target is no longer valid
            message_log.add_message(
                "Pry failed: target no longer valid.",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name()
            )
            return False
            
        # Log the skill activation
        if game.chess_distance(user.y, user.x, target.y, target.x) == 1:
            message_log.add_message(
                f"{user.get_display_name()} pries {target.get_display_name()} skyward with their glaive",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
        else:
            message_log.add_message(
                f"{user.get_display_name()} pries {target.get_display_name()} skyward with their glaive",
                MessageType.ABILITY,
                player=user.player,
                attacker_name=user.get_display_name(),
                target_name=target.get_display_name()
            )
            
            
        # Apply damage to primary target (ignoring defense for part of the damage)
        # This represents the direct impact of hitting the ceiling and ground
        defense_reduced_damage = max(3, self.primary_damage - target.defense)  # 3 damage minimum
        previous_hp = target.hp
        target.hp = max(0, target.hp - defense_reduced_damage)
        
        # Log the primary damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=defense_reduced_damage,
            ability="Pry",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Check for critical health (retching) using centralized logic if target still alive
        if target.is_alive():
            game.check_critical_health(target, user, previous_hp, ui)
            
        # Apply splash damage to adjacent enemy units (secondary debris damage)
        affected_adjacents = []
        
        # Get all units in adjacent squares
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                # Skip the center (primary target)
                if dy == 0 and dx == 0:
                    continue
                
                # Check adjacent position
                adj_y = target.y + dy
                adj_x = target.x + dx
                
                # Validate position
                if not game.is_valid_position(adj_y, adj_x):
                    continue
                
                # Check if there's a unit at this position
                adjacent_unit = game.get_unit_at(adj_y, adj_x)
                if adjacent_unit and adjacent_unit.is_alive() and adjacent_unit.player != user.player:
                    # Apply splash damage (reduced by defense)
                    splash_damage = max(1, self.splash_damage - adjacent_unit.defense)
                    adjacent_unit.hp = max(0, adjacent_unit.hp - splash_damage)
                    
                    # Log splash damage
                    message_log.add_combat_message(
                        attacker_name=user.get_display_name(),
                        target_name=adjacent_unit.get_display_name(),
                        damage=splash_damage,
                        ability="Pry Debris",
                        attacker_player=user.player,
                        target_player=adjacent_unit.player
                    )
                    
                    # Add to affected units list for animation
                    affected_adjacents.append((adjacent_unit, splash_damage))
                    
                    # Check if the adjacent unit was defeated and handle death properly
                    if adjacent_unit.hp <= 0:
                        # Use centralized death handling to ensure all systems (like DOMINION) are notified
                        game.handle_unit_death(adjacent_unit, user, cause="pry_splash", ui=ui)
        
        
        
        # Check if primary target is immune to the movement penalty effect
        if target.is_immune_to_effects():
            message_log.add_message(
                f"{target.get_display_name()} is immune to Pry's movement penalty due to Stasiality",
                MessageType.ABILITY,
                player=target.player,  # Use the target's player for correct color coding
                target_name=target.get_display_name()
            )
        else:
            # Apply movement reduction effect to primary target
            from boneglaive.game.upgrades import UpgradeManager
            is_upgraded = UpgradeManager.is_skill_upgraded(user, "Pry")
            move_penalty = -2 if is_upgraded else -1

            target.move_range_bonus += move_penalty

            # Mark the unit with the appropriate Pry status
            if is_upgraded:
                target.was_pried_upgraded = True
                target.pry_upgraded_duration = 2
                target.pry_upgraded_penalty_amount = -2
                message_log.add_message(
                    f"{target.get_display_name()}'s movement is SEVERELY reduced",
                    MessageType.WARNING,
                    player=user.player
                )
            else:
                target.was_pried = True
                target.pry_duration = 2
                target.pry_penalty_amount = -1
                message_log.add_message(
                    f"{target.get_display_name()}'s movement is reduced",
                    MessageType.WARNING,
                    player=user.player
                )

            # Ensure the unit has a boolean flag that's easier to check in the UI
            target.pry_active = True

            # CASE 1: Check if the target is trapped by a Viceroy trap and free them
            if hasattr(target, 'trapped_by') and target.trapped_by is not None:
                # Clear the trap - messaging is handled elsewhere
                target.trapped_by = None

            # CASE 2: Check if the target has trapped other units with Viceroy trap and release them
            for unit in game.units:
                if hasattr(unit, 'trapped_by') and unit.trapped_by == target:
                    # Clear the trap - messaging is handled elsewhere
                    unit.trapped_by = None

            # Log the stagger/impact message
            message_log.add_message(
                f"{target.get_display_name()} is staggered by the impact",
                MessageType.WARNING,  # Use WARNING for negative status effects
                player=user.player,
                target_name=target.get_display_name()
            )
            
        # Check if primary target was defeated and handle death properly
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="vault", ui=ui)
        
        return True


class VaultSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Vault allows the GLAIVEMAN to leap over obstacles and enemies,
    landing in an empty space within range.
    """
    
    def __init__(self):
        super().__init__(
            name="Vault",
            key="V",
            description="Leap over obstacles to any empty position within range, ignoring pathing restrictions.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=2
        )
        self.landing_damage = 4  # Damage to adjacent enemies on landing (when upgraded)
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if Vault can be used on the target position."""
        # Check for upgrade and update range dynamically
        if game:
            from boneglaive.game.upgrades import UpgradeManager
            is_upgraded = UpgradeManager.is_skill_upgraded(user, "Vault")
            self.range = 3 if is_upgraded else 2

        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Check if the target position is valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Target position must be passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        # Target position must be empty (no unit)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # Calculate vault starting position (current or planned move destination)
        # This is used for range validation
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, vault from that position instead
        # NOTE: This is just for validation - the actual execute() will clear move_target
        if user.move_target:
            from_y, from_x = user.move_target

        # NOTE: Vault is an acrobatic leap that ignores pathing restrictions.
        # It does NOT check intermediate positions - that's the whole point!
        # The unit jumps OVER obstacles and other units.

        # Check if any other unit is already planning to teleport to this position
        # (via Vault, Delta Config, Grae Exchange, or any other teleport skill)
        # NOTE: We don't block on move_target - vault will displace if needed
        for other_unit in game.units:
            if (other_unit.is_alive() and other_unit != user):
                # Check for vault targets
                if (hasattr(other_unit, 'vault_target_indicator') and
                    other_unit.vault_target_indicator == target_pos):
                    # Position is already targeted by another unit's vault
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    # Position is already targeted by another unit's teleport
                    return False

        # Check if target is within range (from_y, from_x already calculated above)
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self

        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        # Clear the move target - Vault IS the movement, don't walk first
        user.move_target = None

        # Set vault target indicator for UI
        user.vault_target_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} prepares to vault to position ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )

        self.current_cooldown = self.cooldown
        return True

    def _find_displacement_position(self, game: 'Game', target_pos: tuple) -> tuple:
        """
        Find nearest adjacent empty tile for displacement.

        Args:
            game: Game instance
            target_pos: Original target position (y, x)

        Returns:
            Tuple (y, x) of displacement position, or None if no valid tiles (vault fizzles)
        """
        from boneglaive.utils.coordinates import get_adjacent_positions

        # Get all 8 adjacent positions
        adjacent_positions = get_adjacent_positions(target_pos[0], target_pos[1])

        # Filter for valid displacement positions
        for adj_y, adj_x in adjacent_positions:
            # Must be valid position
            if not game.is_valid_position(adj_y, adj_x):
                continue

            # Must be passable terrain
            if not game.map.is_passable(adj_y, adj_x):
                continue

            # Must be empty (no unit currently there)
            if game.get_unit_at(adj_y, adj_x) is not None:
                continue

            # Must not have another unit moving/vaulting there
            position_blocked = False
            for other_unit in game.units:
                if other_unit.is_alive():
                    # Check for regular move targets
                    if (hasattr(other_unit, 'move_target') and
                        other_unit.move_target == (adj_y, adj_x)):
                        position_blocked = True
                        break

                    # Check for vault targets
                    if (hasattr(other_unit, 'vault_target_indicator') and
                        other_unit.vault_target_indicator == (adj_y, adj_x)):
                        position_blocked = True
                        break

                    # Check for teleport targets
                    if (hasattr(other_unit, 'teleport_target_indicator') and
                        other_unit.teleport_target_indicator == (adj_y, adj_x)):
                        position_blocked = True
                        break

            if not position_blocked:
                # Found valid displacement position
                return (adj_y, adj_x)

        # No valid displacement positions found
        return None

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Vault skill to leap over obstacles to a target position."""
        from boneglaive.utils.message_log import message_log, MessageType

        # SAFETY CHECK: Verify target position is still valid and empty
        # (Another unit might have moved there between planning and execution)
        # If occupied, try to displace to adjacent tile
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            # Try to find displacement position
            displaced_pos = self._find_displacement_position(game, target_pos)

            if displaced_pos is None:
                # No valid adjacent tiles - vault fizzles
                message_log.add_message(
                    f"{user.get_display_name()}'s Vault fizzles - no room to land!",
                    MessageType.WARNING,
                    player=user.player
                )
                # Clear indicators and return failure
                user.vault_target_indicator = None
                return False
            else:
                # Displacement found - update target position
                target_pos = displaced_pos
                # Set flag for visual system to use displaced position
                user.vault_displaced_to = displaced_pos
                # Log displacement message
                message_log.add_message(
                    f"{user.get_display_name()} twists mid-flight, landing at ({displaced_pos[0]}, {displaced_pos[1]})",
                    MessageType.ABILITY,
                    player=user.player
                )

        # Clear the vault target indicator after execution
        user.vault_target_indicator = None

        # Store original position for animations
        original_pos = (user.y, user.x)

        # Check for upgrade to determine animation
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Vault")

        # Play animation if UI is available
        # Apply the vault teleport (atomic position update)
        # Vault is a TELEPORT that ignores pathing - must bypass property setters
        # to avoid intermediate position checks in _update_unit_grid()
        final_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if final_unit is not None and final_unit != user:
            # Target occupied (should have been caught by can_use, but check anyway)
            from boneglaive.utils.debug import logger
            logger.error(f"GLAIVE VAULT BLOCKED: {user.get_display_name()}'s vault to {target_pos} blocked - position occupied by {final_unit.get_display_name()}")
            message_log.add_message(
                f"{user.get_display_name()}'s Glaive Vault blocked - position occupied!",
                MessageType.WARNING,
                player=user.player
            )
            return False

        # Teleport atomically: remove from old position, update coordinates, add to new position
        # This avoids intermediate position checks that would block the vault
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

        # Log the completion of vault
        message_log.add_message(
            f"{user.get_display_name()} vaults from ({original_pos[0]}, {original_pos[1]}) to ({target_pos[0]}, {target_pos[1]})",
            MessageType.ABILITY,
            player=user.player
        )

        # Check for upgrade and apply landing damage
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Vault")

        if is_upgraded:
            # Find adjacent enemies and damage them
            adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            damaged_units = []

            for dy, dx in adjacent_offsets:
                adj_y, adj_x = target_pos[0] + dy, target_pos[1] + dx
                if game.is_valid_position(adj_y, adj_x):
                    adjacent_unit = game.get_unit_at(adj_y, adj_x)
                    if adjacent_unit and adjacent_unit.player != user.player and adjacent_unit.is_alive():
                        # Calculate damage with defense
                        defense_reduced_damage = max(0, self.landing_damage - adjacent_unit.defense)
                        adjacent_unit.hp -= defense_reduced_damage
                        damaged_units.append((adjacent_unit, defense_reduced_damage))

                        message_log.add_message(
                            f"{adjacent_unit.get_display_name()} takes {defense_reduced_damage} landing damage",
                            MessageType.COMBAT,
                            player=user.player,
                            attacker_name=user.get_display_name(),
                            target_name=adjacent_unit.get_display_name()
                        )

                        # Check for death
                        if adjacent_unit.hp <= 0:
                            game.handle_unit_death(adjacent_unit, user, cause="vault", ui=ui)


        return True


class JudgementSkill(ActiveSkill):
    """
    Active skill for GLAIVEMAN.
    Delivers divine judgement via a sacred spinning glaive, dealing piercing damage.
    """
    
    def __init__(self):
        super().__init__(
            name="Judgement",
            key="J",
            description="Throw a sacred glaive at an enemy (range 4). Deals pierce damage that ignores defense.",
            target_type=TargetType.ENEMY,
            cooldown=4,
            range_=4
        )
        self.damage = 4
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Check if target is an enemy unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target or target.player == user.player:
            return False

        # Cannot target untargetable units (e.g., Karrier Rave phasing)
        if target.is_untargetable():
            return False

        # Check if target is within range from the correct position
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target

        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        # Check if there's line of sight to the target
        if not game.has_line_of_sight(from_y, from_x, target_pos[0], target_pos[1]):
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Track action order
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])  
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} readies a sacred glaive to throw at {target.get_display_name()}",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Judgement skill to deliver divine judgment via a sacred spinning glaive."""
        from boneglaive.utils.message_log import message_log, MessageType

        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} hurls a sacred glaive",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name()
        )
        
        # Play animation if UI is available
        # Always show base effect message
        message_log.add_message(
            f"The sacred glaive bypasses {target.get_display_name()}'s defenses",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        # Check if target is at critical health for double damage
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        critical_threshold = int(target.max_hp * CRITICAL_HEALTH_PERCENT)
        is_critical_hit = target.hp <= critical_threshold
        
        # Apply damage with critical bonus if applicable
        base_damage = self.damage  # Base damage
        
        # Double damage if target is at critical health
        if is_critical_hit:
            damage = base_damage * 2  # Critical hit doubles damage
            # Log critical effect
            message_log.add_message(
                f"The sacred glaive strikes with divine judgement",
                MessageType.ABILITY,
                player=user.player,
                target_name=target.get_display_name()
            )
        else:
            damage = base_damage
        
        # Store previous HP for animation
        previous_hp = target.hp
        
        # Apply damage (piercing - ignores defense)
        target.hp = max(0, target.hp - damage)
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Judgement",
            attacker_player=user.player,
            target_player=target.player
        )
        
        
        # Check if target was defeated and handle death properly
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="judgement", ui=ui)

            # Check for Judgement upgrade - refresh cooldown on kill
            from boneglaive.game.upgrades import UpgradeManager
            is_upgraded = UpgradeManager.is_skill_upgraded(user, "Judgement")
            if is_upgraded:
                self.current_cooldown = 0

                # Dramatic message about the glaive returning
                message_log.add_message(
                    f"Divine judgement rendered! The sacred glaive returns to {user.get_display_name()}",
                    MessageType.ABILITY,
                    player=user.player
                )


        return True