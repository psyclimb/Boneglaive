#!/usr/bin/env python3
"""
Skills specific to the MANDIBLE_FOREMAN unit type.
This module contains all passive and active abilities for MANDIBLE_FOREMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Viseroy(PassiveSkill):
    """Passive skill for MANDIBLE_FOREMAN. Traps enemies in mechanical jaws."""
    
    def __init__(self):
        super().__init__(
            name="Viseroy",
            key="V",
            description="When attacking, traps the enemy unit in mechanical jaws. Trapped units cannot move and take damage each turn."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        # Implementation handled in Game engine
        pass


class DischargeSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Renamed to Expedite in the code. Rushes forward in a straight line.
    """
    
    def __init__(self):
        super().__init__(
            name="Expedite",  # Renamed from Discharge to Expedite
            key="E",
            description="Rush up to 4 tiles in a line. Automatically trap and damage the first enemy encountered.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=4
        )
        self.trap_damage = 6
    
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
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} expedites forward!",
            MessageType.ABILITY,
            player=user.player
        )
        user.y, user.x = target_pos
        return True


class SiteInspectionSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Surveys an area, granting bonuses to allies near terrain.
    """
    
    def __init__(self):
        super().__init__(
            name="Site Inspection",
            key="S",
            description="Survey a 3x3 area. Grants movement and attack bonuses to allies.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3,
            area=1
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
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} inspects the site around ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        return True


class JawlineSkill(ActiveSkill):
    """
    Active skill for MANDIBLE_FOREMAN.
    Deploys a network of smaller mechanical jaws in a 3×3 area.
    """
    
    def __init__(self):
        super().__init__(
            name="Jawline",
            key="J",
            description="Deploy network of mechanical jaws in 3x3 area around yourself. Deals 4 damage and reduces enemy movement by 1 for 3 turns.",
            target_type=TargetType.SELF,
            cooldown=5,
            range_=0,
            area=1
        )
        self.damage = 4
        self.effect_duration = 3
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game:
            return False
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # For self-targeted skills, use the unit's position
        target_pos = (user.y, user.x)
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        # Simple implementation for minimal functionality
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} deploys JAWLINE network!",
            MessageType.ABILITY,
            player=user.player
        )
        return True