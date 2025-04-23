#!/usr/bin/env python3
"""
Skills specific to the GRAYMAN unit type.
This module contains all passive and active abilities for GRAYMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType

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
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        # Implementation handled in Unit.is_immune_to_effects()
        pass


class DeltaConfigSkill(ActiveSkill):
    """Active skill for GRAYMAN. Teleports to any unoccupied tile on the map."""
    
    def __init__(self):
        super().__init__(
            name="Delta Config",
            key="D",
            description="Teleport to any unoccupied tile on the map.",
            target_type=TargetType.AREA,
            cooldown=12,
            range_=99
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        original_pos = (user.y, user.x)
        user.y, user.x = target_pos
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} teleports to position ({target_pos[0]}, {target_pos[1]})!",
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
            description="Fire a beam that phases target out of normal spacetime. Target receives -1 to all actions.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )
        self.damage = 2
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        from boneglaive.utils.message_log import message_log, MessageType
        # Apply damage
        target.hp = max(0, target.hp - self.damage)
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=self.damage,
            ability="Estrange",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Apply estranged effect if not immune
        if not target.is_immune_to_effects():
            target.estranged = True
            message_log.add_message(
                f"{target.get_display_name()} is phased out of normal spacetime!",
                MessageType.ABILITY,
                player=user.player
            )
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to Estrange due to Stasiality!",
                MessageType.ABILITY,
                player=user.player
            )
        return True


class GraeExchangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Creates an echo that can attack but not move."""
    
    def __init__(self):
        super().__init__(
            name="Græ Exchange",
            key="G",
            description="Create an echo at current position and teleport away. Echo can attack but not move.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        original_pos = (user.y, user.x)
        user.y, user.x = target_pos
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} creates an echo and teleports to ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        return True