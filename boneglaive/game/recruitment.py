#!/usr/bin/env python3
"""
Unit recruitment system for the setup phase.
Manages the pool of available units and recruitment mechanics.
"""

from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from boneglaive.utils.constants import UnitType
from boneglaive.utils.debug import logger


# Define recruitment order (excluding HEINOUS_VAPOR which is summoned)
RECRUITMENT_ORDER = [
    UnitType.GLAIVEMAN,
    UnitType.GRAYMAN,
    UnitType.MANDIBLE_FOREMAN,
    UnitType.POTPOURRIST,
    UnitType.MARROW_CONDENSER,
    UnitType.INTERFERER,
    UnitType.FOWL_CONTRIVANCE,
    UnitType.DELPHIC_APPRAISER,
    UnitType.GAS_MACHINIST,
    UnitType.DERELICTIONIST
]


class RecruitmentPhase(Enum):
    """Phases of the recruitment process."""
    PLAYER_1_RECRUITING = "player1_recruiting"
    PLAYER_2_RECRUITING = "player2_recruiting"
    COMPLETED = "completed"


@dataclass
class PlayerUnitPool:
    """Tracks the available units for recruitment for a single player."""
    player_id: int
    available_units: Dict[UnitType, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the unit pool with 2 of each unit type."""
        if not self.available_units:
            self.reset_pool()
    
    def reset_pool(self):
        """Reset the pool to have 2 of each unit type."""
        self.available_units = {}

        for unit_type in RECRUITMENT_ORDER:
            self.available_units[unit_type] = 2

        logger.info(f"Player {self.player_id} unit pool reset with {len(RECRUITMENT_ORDER)} unit types, 2 each")
    
    def is_available(self, unit_type: UnitType) -> bool:
        """Check if a unit type is available for recruitment."""
        return self.available_units.get(unit_type, 0) > 0
    
    def get_available_count(self, unit_type: UnitType) -> int:
        """Get the number of available units of a specific type."""
        return self.available_units.get(unit_type, 0)
    
    def get_available_types(self) -> List[UnitType]:
        """Get all unit types that are available for recruitment in the correct order."""
        return [unit_type for unit_type in RECRUITMENT_ORDER if self.available_units.get(unit_type, 0) > 0]
    
    def recruit_unit(self, unit_type: UnitType) -> bool:
        """Recruit a unit, reducing the available count. Returns True if successful."""
        if self.is_available(unit_type):
            self.available_units[unit_type] -= 1
            logger.info(f"Player {self.player_id} recruited {unit_type.name}, {self.available_units[unit_type]} remaining")
            return True
        return False
    
    def return_unit(self, unit_type: UnitType):
        """Return a unit to the pool (for undoing recruitment)."""
        current_count = self.available_units.get(unit_type, 0)
        if current_count < 2:  # Can't have more than 2 of each type
            self.available_units[unit_type] = current_count + 1
            logger.info(f"Player {self.player_id} returned {unit_type.name}, {self.available_units[unit_type]} available")
    
    def get_pool_summary(self) -> Dict[str, int]:
        """Get a summary of the current pool state."""
        return {unit_type.name: count for unit_type, count in self.available_units.items()}


@dataclass
class PlayerRecruitment:
    """Tracks a player's recruitment state."""
    player_id: int
    recruited_units: List[UnitType] = field(default_factory=list)
    max_units: int = 3
    confirmed: bool = False
    
    def can_recruit_more(self) -> bool:
        """Check if the player can recruit more units."""
        return len(self.recruited_units) < self.max_units
    
    def recruit_unit(self, unit_type: UnitType) -> bool:
        """Add a recruited unit to the player's roster."""
        if self.can_recruit_more():
            self.recruited_units.append(unit_type)
            logger.info(f"Player {self.player_id} recruited {unit_type.name}")
            return True
        return False
    
    def remove_unit(self, index: int) -> Optional[UnitType]:
        """Remove a unit from the player's roster by index."""
        if 0 <= index < len(self.recruited_units):
            unit_type = self.recruited_units.pop(index)
            logger.info(f"Player {self.player_id} removed {unit_type.name}")
            return unit_type
        return None
    
    def is_complete(self) -> bool:
        """Check if the player has recruited the maximum number of units."""
        return len(self.recruited_units) >= self.max_units
    
    def confirm_recruitment(self):
        """Confirm the player's recruitment choices."""
        self.confirmed = True
        logger.info(f"Player {self.player_id} confirmed recruitment")
    
    def reset(self):
        """Reset the player's recruitment state."""
        self.recruited_units = []
        self.confirmed = False


class RecruitmentSystem:
    """Manages the unit recruitment process for both players."""
    
    def __init__(self):
        self.player1_pool = PlayerUnitPool(1)
        self.player2_pool = PlayerUnitPool(2)
        self.player1 = PlayerRecruitment(1)
        self.player2 = PlayerRecruitment(2)
        self.current_phase = RecruitmentPhase.PLAYER_1_RECRUITING
        
    def reset_recruitment(self):
        """Reset the entire recruitment system for a new game."""
        self.player1_pool.reset_pool()
        self.player2_pool.reset_pool()
        self.player1.reset()
        self.player2.reset()
        self.current_phase = RecruitmentPhase.PLAYER_1_RECRUITING
        logger.info("Recruitment system reset")
    
    def get_current_player(self) -> Optional[PlayerRecruitment]:
        """Get the player currently recruiting."""
        if self.current_phase == RecruitmentPhase.PLAYER_1_RECRUITING:
            return self.player1
        elif self.current_phase == RecruitmentPhase.PLAYER_2_RECRUITING:
            return self.player2
        return None
    
    def get_player(self, player_id: int) -> Optional[PlayerRecruitment]:
        """Get a specific player's recruitment data."""
        if player_id == 1:
            return self.player1
        elif player_id == 2:
            return self.player2
        return None
    
    def get_current_player_pool(self) -> Optional[PlayerUnitPool]:
        """Get the unit pool for the currently active player."""
        if self.current_phase == RecruitmentPhase.PLAYER_1_RECRUITING:
            return self.player1_pool
        elif self.current_phase == RecruitmentPhase.PLAYER_2_RECRUITING:
            return self.player2_pool
        return None
    
    def recruit_unit_for_current_player(self, unit_type: UnitType) -> bool:
        """Recruit a unit for the currently active player."""
        current_player = self.get_current_player()
        current_pool = self.get_current_player_pool()
        if not current_player or not current_pool or not current_player.can_recruit_more():
            return False
        
        if current_pool.recruit_unit(unit_type):
            current_player.recruit_unit(unit_type)
            return True
        return False
    
    def remove_unit_for_current_player(self, index: int) -> bool:
        """Remove a recruited unit for the currently active player."""
        current_player = self.get_current_player()
        current_pool = self.get_current_player_pool()
        if not current_player or not current_pool:
            return False
        
        unit_type = current_player.remove_unit(index)
        if unit_type:
            current_pool.return_unit(unit_type)
            return True
        return False
    
    def confirm_current_player(self) -> bool:
        """Confirm recruitment for the current player and advance phase."""
        current_player = self.get_current_player()
        if not current_player or not current_player.is_complete():
            return False
        
        current_player.confirm_recruitment()
        
        # Advance to next phase
        if self.current_phase == RecruitmentPhase.PLAYER_1_RECRUITING:
            self.current_phase = RecruitmentPhase.PLAYER_2_RECRUITING
            logger.info("Advanced to Player 2 recruitment")
        elif self.current_phase == RecruitmentPhase.PLAYER_2_RECRUITING:
            self.current_phase = RecruitmentPhase.COMPLETED
            logger.info("Recruitment completed")
        
        return True
    
    def is_recruitment_complete(self) -> bool:
        """Check if recruitment is complete for both players."""
        return self.current_phase == RecruitmentPhase.COMPLETED
    
    def can_start_game(self) -> bool:
        """Check if the game can start (both players have confirmed)."""
        return (self.player1.confirmed and self.player2.confirmed and 
                self.is_recruitment_complete())
    
    def get_recruitment_summary(self) -> Dict:
        """Get a summary of the current recruitment state."""
        return {
            'phase': self.current_phase.value,
            'player1_pool': self.player1_pool.get_pool_summary(),
            'player2_pool': self.player2_pool.get_pool_summary(),
            'player1': {
                'recruited': [unit.name for unit in self.player1.recruited_units],
                'count': len(self.player1.recruited_units),
                'max': self.player1.max_units,
                'confirmed': self.player1.confirmed,
                'can_recruit_more': self.player1.can_recruit_more()
            },
            'player2': {
                'recruited': [unit.name for unit in self.player2.recruited_units],
                'count': len(self.player2.recruited_units),
                'max': self.player2.max_units,
                'confirmed': self.player2.confirmed,
                'can_recruit_more': self.player2.can_recruit_more()
            }
        }


# Global recruitment system instance
recruitment_system = RecruitmentSystem()