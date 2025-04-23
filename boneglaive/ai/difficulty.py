#!/usr/bin/env python3
"""
Difficulty level implementations for AI.
"""

import random
from typing import Optional, Dict, Any

from boneglaive.ai.decision import Decision
from boneglaive.utils.debug import logger

class DifficultyManager:
    """
    Manages the application of difficulty-based adjustments to AI decisions.
    Different difficulty levels have different chances of making mistakes or
    suboptimal decisions.
    """
    
    def __init__(self, difficulty: str = "medium"):
        """
        Initialize the difficulty manager.
        
        Args:
            difficulty: The difficulty level ("easy", "medium", "hard")
        """
        self.difficulty = difficulty.lower()
        
        # Probability of making a random decision instead of the optimal one
        self.randomness_factor = self._get_randomness_factor()
        
        # Whether the AI should consider using skills or only basic attacks
        self.use_skills = self._should_use_skills()
        
        # Whether the AI should prioritize attacking damaged units
        self.target_damaged_units = self._should_target_damaged_units()
        
        logger.info(f"Initialized AI difficulty: {difficulty}")
        logger.debug(f"Randomness factor: {self.randomness_factor}")
        logger.debug(f"Use skills: {self.use_skills}")
        logger.debug(f"Target damaged units: {self.target_damaged_units}")
        
    def _get_randomness_factor(self) -> float:
        """
        Get the randomness factor based on difficulty.
        This determines how often the AI will make a sub-optimal decision.
        
        Returns:
            Float between 0 and 1, where higher means more randomness
        """
        if self.difficulty == "easy":
            return 0.5  # 50% chance of random decision
        elif self.difficulty == "medium":
            return 0.2  # 20% chance of random decision
        elif self.difficulty == "hard":
            return 0.05  # 5% chance of random decision
        else:
            # Default to medium
            return 0.2
            
    def _should_use_skills(self) -> bool:
        """
        Determine if the AI should use skills based on difficulty.
        
        Returns:
            True if the AI should use skills, False otherwise
        """
        if self.difficulty == "easy":
            return random.random() > 0.5  # 50% chance of using skills
        elif self.difficulty == "medium":
            return True  # Always use skills on medium
        elif self.difficulty == "hard":
            return True  # Always use skills on hard
        else:
            # Default to medium behavior
            return True
            
    def _should_target_damaged_units(self) -> bool:
        """
        Determine if the AI should prioritize targeting damaged units.
        
        Returns:
            True if the AI should target damaged units, False otherwise
        """
        if self.difficulty == "easy":
            return False  # Don't prioritize on easy
        elif self.difficulty == "medium":
            return random.random() > 0.3  # 70% chance of prioritizing
        elif self.difficulty == "hard":
            return True  # Always prioritize on hard
        else:
            # Default to medium behavior
            return random.random() > 0.3
            
    def apply_difficulty(self, decisions: list[Decision]) -> Optional[Decision]:
        """
        Apply difficulty-based adjustments to a list of decisions.
        
        Args:
            decisions: List of Decision objects, assumed to be sorted by score
                      (highest score first)
                      
        Returns:
            A Decision object, potentially modified by difficulty settings
        """
        if not decisions:
            return None
            
        # For hard difficulty, almost always choose the best decision
        if self.difficulty == "hard" and random.random() > self.randomness_factor:
            return decisions[0]
            
        # For easier difficulties, maybe pick a sub-optimal decision
        if random.random() < self.randomness_factor:
            # Pick a random decision from the list
            return random.choice(decisions)
            
        # Otherwise, choose the best decision
        return decisions[0]