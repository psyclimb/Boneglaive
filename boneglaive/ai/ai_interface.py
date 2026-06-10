#!/usr/bin/env python3
"""
AI interface for Boneglaive.
Provides a clean interface between the game and AI controllers.
"""

from typing import Optional, TYPE_CHECKING
from boneglaive.utils.debug import logger
from boneglaive.utils.config import ConfigManager

if TYPE_CHECKING:
    from boneglaive.game.engine import Game
    from boneglaive.ui.game_ui import GameUI

class AIInterface:
    """
    Interface for AI controllers.
    Used by the multiplayer manager to handle AI turns.
    """

    def __init__(self):
        """Initialize the AI interface."""
        self.game = None
        self.ui = None
        self.initialized = False
        self.ai_controller = None
        self.config = ConfigManager()

    def initialize(self, game: 'Game', ui: Optional['GameUI'] = None) -> bool:
        """
        Initialize the AI interface with a game instance.

        Args:
            game: The Game instance
            ui: Optional UI reference for animations

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.game = game
            self.ui = ui

            # Import and initialize the AI controller
            # Use SmartAI for intelligent decision-making
            from boneglaive.ai.smart_ai import SmartAI
            self.ai_controller = SmartAI(game, ui)

            logger.info("AI interface initialized successfully")
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AI interface: {e}")
            self.initialized = False
            return False

    def process_turn(self) -> bool:
        """
        Process an AI turn.

        Returns:
            True if the turn was processed successfully, False otherwise
        """
        if not self.initialized or not self.ai_controller:
            logger.error("AI interface not properly initialized")
            return False

        try:
            result = self.ai_controller.process_turn()
            return result
        except Exception as e:
            logger.error(f"Error processing AI turn: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources used by the AI."""
        self.game = None
        self.ui = None
        self.ai_controller = None
        self.initialized = False
