#!/usr/bin/env python3
"""
Skills specific to the INTERFERER unit type.
This module contains all passive and active abilities for INTERFERER units.
"""


from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType
if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class NeutronIlluminant(PassiveSkill):
    """
    Passive skill for INTERFERER.
    On successful attack, the antenna array energizes the carabiners, causing RF burn that spreads directionally.
    Cardinal attacks radiate diagonally, diagonal attacks radiate cardinally.
    """

    def __init__(self):
        super().__init__(
            name="Radio Effulgent",
            key="N",
            description="On attack, the antenna array energizes the carabiners, causing RF burn that spreads directionally. Cardinal attacks radiate diagonally, diagonal attacks radiate cardinally. 1 damage/turn for 2 turns per stack."
        )
        self.current_cooldown = 0
        self.cooldown = 0  # No cooldown
        
    def apply_passive(self, user: 'Unit', game=None, ui=None) -> None:
        """Apply effects of the passive skill."""
        # This is handled by the game engine when attacks are processed
        pass
    
    def tick_cooldown(self) -> None:
        """Reduce cooldown by 1 turn."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
    
    def can_trigger(self) -> bool:
        """Check if the passive can trigger (not on cooldown)."""
        return self.current_cooldown == 0
    
    def _get_radiation_positions(self, user: 'Unit', target_pos: tuple) -> list:
        """Get radiation positions based on attack direction."""
        # Calculate attack direction
        dy = target_pos[0] - user.y
        dx = target_pos[1] - user.x
        
        # Normalize direction for pattern determination
        is_cardinal = (dy == 0 or dx == 0)
        
        if is_cardinal:
            # Cardinal attack -> radiate diagonally around INTERFERER
            return [
                (user.y - 1, user.x - 1),  # Up-left of INTERFERER
                (user.y - 1, user.x + 1),  # Up-right of INTERFERER
                (user.y + 1, user.x - 1),  # Down-left of INTERFERER
                (user.y + 1, user.x + 1)   # Down-right of INTERFERER
            ]
        else:
            # Diagonal attack -> radiate cardinally around INTERFERER
            return [
                (user.y - 1, user.x),      # Up from INTERFERER
                (user.y + 1, user.x),      # Down from INTERFERER
                (user.y, user.x - 1),      # Left from INTERFERER
                (user.y, user.x + 1)       # Right from INTERFERER
            ]

    def trigger_radiation(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> None:
        """Trigger radiation burn in directional pattern around the INTERFERER."""
        if not self.can_trigger():
            return

        # Set cooldown (0, so always triggers)
        self.current_cooldown = self.cooldown

        # Check if Radio Effulgent is upgraded
        from boneglaive.game.upgrades import UpgradeManager
        neutron_upgraded = UpgradeManager.is_skill_upgraded(user, "Radio Effulgent")

        # Get radiation positions
        radiation_positions = self._get_radiation_positions(user, target_pos)

        # With upgrade: Also flash the primary target
        if neutron_upgraded:
            primary_target = game.get_unit_at(target_pos[0], target_pos[1])
            if primary_target and primary_target.player != user.player and primary_target.is_alive():
                if not primary_target.is_immune_to_effects():
                    if not hasattr(primary_target, 'radiation_stacks'):
                        primary_target.radiation_stacks = []
                    primary_target.radiation_stacks.append(2)

        # Apply radiation to valid positions
        affected_units = []
        immune_units = []
        for pos in radiation_positions:
            y, x = pos
            if not game.is_valid_position(y, x):
                continue

            target = game.get_unit_at(y, x)
            if target and target.player != user.player and target.is_alive():
                # Check if target is immune to radiation (GRAYMAN with Stasiality)
                if target.is_immune_to_effects():
                    immune_units.append(target)
                    continue

                # Apply radiation burn
                if not hasattr(target, 'radiation_stacks'):
                    target.radiation_stacks = []

                # Add new radiation stack (2 turns duration)
                target.radiation_stacks.append(2)
                affected_units.append(target)

        # Log radiation effect only if units were affected
        if affected_units:
            message_log.add_message(
                f"RF energy radiates from the impact",
                MessageType.WARNING,
                player=user.player
            )

        # Log immunity message for immune units
        for immune_unit in immune_units:
            message_log.add_message(
                f"{immune_unit.get_display_name()} is immune to RF burn due to Stasiality",
                MessageType.ABILITY,
                player=immune_unit.player
            )


class NeuralShuntSkill(ActiveSkill):
    """
    Active skill for INTERFERER.
    Neural disruption causes target to perform random actions.
    """
    
    def __init__(self):
        super().__init__(
            name="Neural Shunt",
            key="N",
            description="Neural disruption attack (range 1). Deals 6 damage and causes target to perform random actions for 1 turn.",
            target_type=TargetType.ENEMY,
            cooldown=4,
            range_=1
        )
        self.damage = 6
        self.effect_duration = 1

    def get_range(self, user: 'Unit') -> int:
        """Get effective range based on upgrade status."""
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Neural Shunt"):
            return 3
        return self.range
    
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

        # Check range (use get_range for upgrade support)
        from_y = user.y
        from_x = user.x
        if user.move_target:
            from_y, from_x = user.move_target

        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        effective_range = self.get_range(user)
        if distance > effective_range:
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
        
        target = game.get_unit_at(target_pos[0], target_pos[1])
        message_log.add_message(
            f"{user.get_display_name()} coordinates a neural interference triangulation",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Neural Shunt skill."""
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
        
        
        
        # Apply damage (increased by 2 if upgraded)
        from boneglaive.game.upgrades import UpgradeManager
        is_upgraded = UpgradeManager.is_skill_upgraded(user, "Neural Shunt")
        base_damage = self.damage + 2 if is_upgraded else self.damage
        damage = max(1, base_damage - target.defense)
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Neural Shunt",
            attacker_player=user.player,
            target_player=target.player
        )
        
        
        if target.hp <= 0:
            # Use centralized death handling to ensure all systems (like DOMINION) are notified
            game.handle_unit_death(target, user, cause="neural_shunt", ui=ui)
        else:
            # Check for critical health
            game.check_critical_health(target, user, previous_hp, ui)
            
            # Apply neural shunt effect if target survives and not immune
            if target.is_immune_to_effects():
                message_log.add_message(
                    f"{target.get_display_name()} is immune to Neural Shunt due to Stasiality",
                    MessageType.ABILITY,
                    player=target.player,
                    target_name=target.get_display_name()
                )
            else:
                target.neural_shunt_affected = True
                target.neural_shunt_duration = self.effect_duration
                
                message_log.add_message(
                    f"{target.get_display_name()}'s actions become erratic",
                    MessageType.WARNING,
                    player=user.player,
                    target_name=target.get_display_name()
                )
        
        return True


class KarrierRaveSkill(ActiveSkill):
    """
    Active skill for INTERFERER.
    Becomes untargetable and next attack strikes 3 times.
    """
    
    def __init__(self):
        super().__init__(
            name="Karrier Rave",
            key="K",
            description="Phase out of reality for 2 turns. Become untargetable, but cannot attack. Next attack after phasing strikes 3 times.",
            target_type=TargetType.SELF,
            cooldown=6,
            range_=0
        )
        self.effect_duration = 2
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        return True
    
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
            
        # For self-targeted skills, use current position
        if user.move_target:
            target_pos = user.move_target
        else:
            target_pos = (user.y, user.x)
            
        user.skill_target = target_pos
        user.selected_skill = self
        
        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1
        
        message_log.add_message(
            f"{user.get_display_name()} synchronizes with the karrier wave transmission",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Karrier Rave skill."""
        message_log.add_message(
            f"{user.get_display_name()} rides the karrier wave out of phase",
            MessageType.ABILITY,
            player=user.player
        )
        
        
        # Apply karrier rave effect
        user.carrier_rave_active = True
        user.carrier_rave_duration = self.effect_duration
        user.carrier_rave_strikes_ready = False  # Will be set to True when effect ends
        
        message_log.add_message(
            f"{user.get_display_name()} becomes untargetable",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True


class ScalarNodeSkill(ActiveSkill):
    """
    Active skill for INTERFERER.
    Places invisible traps that deal damage when triggered.
    """
    
    def __init__(self):
        super().__init__(
            name="Scalar Node",
            key="S",
            description="Place invisible trap on empty terrain (range 3). Triggers when enemy ends turn on tile, dealing 8 damage. Silent deployment and activation.",
            target_type=TargetType.AREA,
            cooldown=2,
            range_=3
        )
        self.damage = 8

    def get_range(self, user: 'Unit') -> int:
        """Get effective range based on upgrade status."""
        from boneglaive.game.upgrades import UpgradeManager
        if UpgradeManager.is_skill_upgraded(user, "Scalar Node"):
            return 4  # Upgraded: range 4
        return self.range  # Base: range 3

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Must target empty, passable terrain
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False
            
        # Check range
        from_y = user.y
        from_x = user.x
        if user.move_target:
            from_y, from_x = user.move_target
            
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.get_range(user):
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
        
        # Silent deployment - no message log entry
        
        self.current_cooldown = self.cooldown
        return True
    
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute Scalar Node placement."""
        # Silent deployment - no message log entries
        
        # Create scalar node tracking in game
        if not hasattr(game, 'scalar_nodes'):
            game.scalar_nodes = {}
            
        # Place the node
        game.scalar_nodes[target_pos] = {
            'owner': user,
            'damage': self.damage,
            'active': True
        }
        
        # No visual indication - completely invisible
        # No animation or message log entries for psychological warfare
        
        return True