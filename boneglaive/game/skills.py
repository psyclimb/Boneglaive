#!/usr/bin/env python3
"""
Skills and abilities system for Boneglaive units.
This module provides the foundation for implementing unit skills.
"""

from enum import Enum, auto
from typing import Optional, Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class SkillType(Enum):
    """Types of skills available to units."""
    PASSIVE = auto()    # Always active
    ACTIVE = auto()     # Activated by the player


class TargetType(Enum):
    """Types of targets for skills."""
    SELF = auto()       # Targets the unit itself
    ALLY = auto()       # Targets a single ally
    ENEMY = auto()      # Targets a single enemy
    AREA = auto()       # Targets an area
    NONE = auto()       # No target needed


class Skill:
    """Base class for all skills."""
    
    def __init__(self, 
                 name: str, 
                 key: str,  # Single key used to activate the skill
                 description: str,
                 skill_type: SkillType,
                 target_type: TargetType,
                 cooldown: int = 0,
                 range_: int = 0,
                 area: int = 0):
        self.name = name
        self.key = key
        self.description = description
        self.skill_type = skill_type
        self.target_type = target_type
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.range = range_  # How far the skill can be used
        self.area = area     # Area of effect (0 for single target)
        
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Check if the skill can be used."""
        # Check cooldown
        if self.current_cooldown > 0:
            return False
            
        # Additional checks can be implemented in subclasses
        return True
        
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        """Use the skill. Return True if successful."""
        if not self.can_use(user, target_pos, game):
            return False
            
        # Set cooldown
        self.current_cooldown = self.cooldown
        
        # Skill effect implemented in subclasses
        return True
        
    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None) -> None:
        """Apply passive effect. Override in passive skill subclasses."""
        pass
        
    def tick_cooldown(self) -> None:
        """Reduce cooldown by 1."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class PassiveSkill(Skill):
    """Base class for passive skills that are always active."""
    
    def __init__(self, name: str, key: str, description: str):
        super().__init__(
            name=name,
            key=key,
            description=description,
            skill_type=SkillType.PASSIVE,
            target_type=TargetType.NONE,
            cooldown=0,
            range_=0,
            area=0
        )


class ActiveSkill(Skill):
    """Base class for active skills that the player can use."""
    
    def __init__(self, name: str, key: str, description: str, target_type: TargetType, 
                 cooldown: int, range_: int, area: int = 0):
        super().__init__(
            name=name,
            key=key,
            description=description,
            skill_type=SkillType.ACTIVE,
            target_type=target_type,
            cooldown=cooldown,
            range_=range_,
            area=area
        )


# Placeholder skill classes for GLAIVEMAN
class Autoclave(PassiveSkill):
    """Passive skill for GLAIVEMAN."""
    
    def __init__(self):
        super().__init__(
            name="Autoclave",
            key="A",
            description="Retaliation skill - implementation details to be defined."
        )


class PrySkill(ActiveSkill):
    """Active skill for GLAIVEMAN."""
    
    def __init__(self):
        super().__init__(
            name="Pry",
            key="P",
            description="Attack skill - implementation details to be defined.",
            target_type=TargetType.ENEMY,
            cooldown=2,
            range_=1
        )


class VaultSkill(ActiveSkill):
    """Active skill for GLAIVEMAN."""
    
    def __init__(self):
        super().__init__(
            name="Vault",
            key="V",
            description="Movement skill - implementation details to be defined.",
            target_type=TargetType.AREA,
            cooldown=3,
            range_=3
        )


# Skill Registry - maps unit types to their skills
UNIT_SKILLS = {
    'GLAIVEMAN': {
        'passive': Autoclave(),
        'active': [PrySkill(), VaultSkill()]
    }
    # Other unit types will be added here
}