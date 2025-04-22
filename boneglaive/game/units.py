#!/usr/bin/env python3
"""
Unit classes and related functionality for Boneglaive.
"""
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from boneglaive.utils.constants import UNIT_STATS, UnitType, MAX_LEVEL, XP_PER_LEVEL

if TYPE_CHECKING:
    from boneglaive.game.skills import Skill, PassiveSkill, ActiveSkill
    from boneglaive.game.engine import Game

class Unit:
    """Base class for all units in the game."""
    
    def __init__(self, unit_type, player, y, x):
        # Basic unit properties
        self.type = unit_type
        self.player = player  # 1 or 2
        self.y = y
        self.x = x
        
        # Greek letter identifier (assigned later when all units are spawned)
        self.greek_id = None
        
        # Get base stats from constants
        base_hp, base_attack, base_defense, base_move_range, base_attack_range = UNIT_STATS[unit_type]
        
        # Current and maximum stats
        self.max_hp = base_hp
        self.hp = self.max_hp
        self.attack = base_attack
        self.defense = base_defense
        self.move_range = base_move_range
        self.attack_range = base_attack_range
        
        # Stat bonuses from skills/items/etc.
        self.hp_bonus = 0
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.move_range_bonus = 0
        self.attack_range_bonus = 0
        
        # Action targets
        self.move_target = None
        self.attack_target = None
        self.skill_target = None
        self.selected_skill = None
        
        # Visual indicators for skills
        self.vault_target_indicator = None  # Visual indicator for Vault destination
        self.site_inspection_indicator = None  # Visual indicator for Site Inspection area
        self.teleport_target_indicator = None  # Visual indicator for Delta Config destination
        
        # Action order tracking (lower is earlier)
        self.action_timestamp = 0
        
        # Status effects
        self.was_pried = False  # Track if this unit was affected by Pry skill
        self.trapped_by = None  # Reference to MANDIBLE_FOREMAN that trapped this unit, None if not trapped
        self.took_action = False  # Track if this unit took an action this turn
        self.jawline_affected = False  # Track if unit is affected by Jawline skill
        self.jawline_duration = 0  # Duration remaining for Jawline effect
        # Removed Recalibrate tracking
        
        # Removed special cooldown trackers
        
        # Experience and leveling
        self.level = 1
        self.xp = 0
        
        # Skills (will be initialized after import to avoid circular imports)
        self.passive_skill = None
        self.active_skills = []
        
    def initialize_skills(self) -> None:
        """Initialize skills for this unit based on its type."""
        # Avoid circular imports
        from boneglaive.game.skills import UNIT_SKILLS
        
        # Get skills from registry if available
        unit_type_name = self.type.name
        if unit_type_name in UNIT_SKILLS:
            skill_set = UNIT_SKILLS[unit_type_name]
            
            # Set passive skill - create new instance for each unit
            if 'passive' in skill_set:
                passive_class = skill_set['passive'].__class__
                self.passive_skill = passive_class()
                
            # Set active skills - create new instances for each unit
            if 'active' in skill_set:
                self.active_skills = []
                for skill in skill_set['active']:
                    # Create a new instance of the skill for this unit
                    skill_class = skill.__class__
                    self.active_skills.append(skill_class())
    
    def is_alive(self) -> bool:
        """Check if the unit is alive."""
        return self.hp > 0
    
    def get_effective_stats(self) -> Dict[str, int]:
        """Get the unit's effective stats including bonuses."""
        return {
            'hp': self.max_hp + self.hp_bonus,
            'attack': self.attack + self.attack_bonus,
            'defense': self.defense + self.defense_bonus,
            'move_range': self.move_range + self.move_range_bonus,
            'attack_range': self.attack_range + self.attack_range_bonus
        }
        
    def get_display_name(self) -> str:
        """Get the unit's display name including the Greek identifier."""
        # Format unit type name for display (replace underscores with spaces)
        display_type = self.type.name
        if display_type == "MANDIBLE_FOREMAN":
            display_type = "MANDIBLE FOREMAN"
            
        if self.greek_id:
            return f"{display_type} {self.greek_id}"
        else:
            return f"{display_type}"
    
    def apply_passive_skills(self, game=None) -> None:
        """Apply effects of passive skills."""
        if self.passive_skill:
            self.passive_skill.apply_passive(self, game)
    
    def get_available_skills(self) -> List:
        """
        Get list of available active skills (not on cooldown).
        """
        # Just check cooldown for all skills
        return [skill for skill in self.active_skills if skill.current_cooldown == 0]
    
    def tick_cooldowns(self) -> None:
        """
        Reduce cooldowns for all skills by 1 turn.
        This is called at the end of a player's turn, only for that player's units.
        A skill with cooldown=1 can be used every turn, cooldown=2 every other turn, etc.
        Movement penalties are handled separately in reset_movement_penalty.
        """
        # Tick skill cooldowns
        for skill in self.active_skills:
            skill.tick_cooldown()
        
        # Movement penalties are now handled in reset_movement_penalty method
        # which is called at the beginning of a player's turn
    
    def add_xp(self, amount: int) -> bool:
        """
        Add XP to the unit and level up if threshold reached.
        Returns True if unit leveled up.
        
        Note: Currently disabled - no XP gain will occur.
        """
        # XP gain is temporarily disabled
        return False
    
    def level_up(self) -> None:
        """Increase unit level and improve stats."""
        if self.level >= MAX_LEVEL:
            return
            
        self.level += 1
        
        # Improve stats based on unit type (can be customized per unit type)
        if self.type == UnitType.GLAIVEMAN:
            self.max_hp += 5
            self.attack += 2
            self.defense += 2
        elif self.type == UnitType.ARCHER:
            self.max_hp += 3
            self.attack += 3
            self.defense += 1
        elif self.type == UnitType.MAGE:
            self.max_hp += 2
            self.attack += 4
            self.defense += 1
        elif self.type == UnitType.MANDIBLE_FOREMAN:
            self.max_hp += 6  # Focus on increasing durability
            self.attack += 2
            self.defense += 3
        
        # Heal unit when leveling up
        self.hp = self.max_hp
        
    def reset_action_targets(self) -> None:
        """Reset all action targets."""
        # Check if the unit took any action this turn that should release trapped units
        # For MANDIBLE_FOREMAN, using Recalibrate shouldn't count as an action that releases trapped units
        
        # By default, any movement, attack, or skill use counts as an action
        took_action = (self.move_target is not None or 
                      self.attack_target is not None or 
                      self.skill_target is not None)
                      
        # No special cases anymore
            
        # Set the took_action flag
        self.took_action = took_action
        
        # Clear all action targets
        self.move_target = None
        self.attack_target = None
        self.skill_target = None
        self.selected_skill = None
        
        # Clear visual indicators
        self.vault_target_indicator = None
        self.site_inspection_indicator = None
        self.teleport_target_indicator = None
        
        self.action_timestamp = 0  # Reset the action timestamp
        # No Recalibrate tracking
        
    def reset_movement_penalty(self) -> None:
        """Clear any movement penalties and reset relevant status flags."""
        # Do not reset move_range_bonus if affected by Jawline
        if not self.jawline_affected and self.move_range_bonus < 0:
            self.move_range_bonus = 0
            
        # Handle Jawline duration if affected
        if self.jawline_affected:
            self.jawline_duration -= 1
            
            # If duration expires, clear the effect
            if self.jawline_duration <= 0:
                from boneglaive.utils.message_log import message_log, MessageType
                self.jawline_affected = False
                # Only restore movement if not affected by other penalties
                if not self.was_pried and self.trapped_by is None:
                    self.move_range_bonus += 1  # Restore the movement penalty
                
                message_log.add_message(
                    f"{self.get_display_name()} breaks free from Jawline tether!",
                    MessageType.ABILITY,
                    target_name=self.get_display_name()
                )
                
        self.was_pried = False
        
    def get_skill_by_key(self, key: str) -> Optional:
        """Get an active skill by its key (for UI selection)."""
        key = key.upper()
        for skill in self.active_skills:
            if skill.key.upper() == key:
                return skill
        return None