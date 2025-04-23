#!/usr/bin/env python3
"""
Decision representation for AI.
This module provides classes for representing AI decisions.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

class ActionType(Enum):
    """Types of actions an AI can take."""
    MOVE = auto()
    ATTACK = auto()
    SKILL = auto()
    WAIT = auto()  # Do nothing
    END_TURN = auto()

@dataclass
class Decision:
    """
    Represents a decision made by the AI.
    This is a placeholder that will be expanded in future implementations.
    """
    action_type: ActionType
    unit_id: int  # Unique identifier for the unit
    target_pos: Optional[Tuple[int, int]] = None
    skill_name: Optional[str] = None
    score: float = 0.0  # Higher is better
    
    def __str__(self) -> str:
        """String representation of the decision."""
        if self.action_type == ActionType.MOVE:
            return f"MOVE unit {self.unit_id} to {self.target_pos}"
        elif self.action_type == ActionType.ATTACK:
            return f"ATTACK with unit {self.unit_id} at {self.target_pos}"
        elif self.action_type == ActionType.SKILL:
            return f"USE SKILL {self.skill_name} with unit {self.unit_id} at {self.target_pos}"
        elif self.action_type == ActionType.WAIT:
            return f"WAIT with unit {self.unit_id}"
        elif self.action_type == ActionType.END_TURN:
            return "END TURN"
        else:
            return f"UNKNOWN ACTION {self.action_type}"