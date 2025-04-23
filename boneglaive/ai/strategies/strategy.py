#!/usr/bin/env python3
"""
Base strategy interface for AI.
Defines the common interface for all AI strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

from boneglaive.game.engine import Game
from boneglaive.game.units import Unit
from boneglaive.ai.decision import Decision

class Strategy(ABC):
    """
    Abstract base class for AI strategies.
    All specific strategies should inherit from this class.
    """
    
    def __init__(self, difficulty: str = "medium"):
        """
        Initialize the strategy.
        
        Args:
            difficulty: The difficulty level ("easy", "medium", "hard")
        """
        self.difficulty = difficulty
    
    @abstractmethod
    def get_best_action(self, game: Game, unit: Unit) -> Optional[Decision]:
        """
        Get the best action for a unit based on the current game state.
        
        Args:
            game: The current Game instance
            unit: The Unit to get an action for
            
        Returns:
            A Decision object representing the best action, or None if no action is possible
        """
        pass