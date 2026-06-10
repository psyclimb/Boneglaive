#!/usr/bin/env python3
"""
Manages multiplayer functionality for the game.
Handles different game modes: single player, local multiplayer, and VS AI.
"""

from typing import Optional

from boneglaive.game.engine import Game
from boneglaive.ai.ai_interface import AIInterface
from boneglaive.utils.config import ConfigManager, NetworkMode
from boneglaive.utils.debug import logger
from boneglaive.utils.message_log import message_log, MessageType

class MultiplayerManager:
    """
    Manages multiplayer functionality, connecting the game engine
    with the appropriate game mode (single player, local multiplayer, or VS AI).
    """

    def __init__(self, game: Game):
        self.game = game
        self.config = ConfigManager()
        self.ai_interface: Optional[AIInterface] = None
        self.initialized = False
        self.current_player = 1
        self._is_local_multiplayer = False

        # Initialize appropriate mode based on config
        self._initialize_mode()

    def _initialize_mode(self) -> bool:
        """Initialize the appropriate game mode."""
        network_mode = self.config.get('network_mode')

        if network_mode == NetworkMode.SINGLE_PLAYER.value:
            logger.info("Initializing single player mode")
            self.game.local_multiplayer = False
            self.initialized = True
            return True

        elif network_mode == NetworkMode.LOCAL_MULTIPLAYER.value:
            logger.info("Initializing local multiplayer")
            self._is_local_multiplayer = True
            self.game.local_multiplayer = True
            self.initialized = True
            logger.info("Local multiplayer initialized successfully")
            return True

        elif network_mode == NetworkMode.VS_AI.value:
            logger.info("Initializing VS AI mode")
            self.ai_interface = AIInterface()
            result = self.ai_interface.initialize(self.game, ui=getattr(self.game, 'ui', None))
            self.initialized = result

            if result:
                self.game.local_multiplayer = False
                logger.info("VS AI mode initialized successfully")
            else:
                logger.error("Failed to initialize VS AI mode")

            return result

        else:
            logger.error(f"Unknown network mode: {network_mode}")
            self.initialized = False
            return False

    def is_current_player_turn(self) -> bool:
        """Check if it's the current player's turn."""
        # Both local multiplayer and single player always return true
        # since both players are on the same computer
        return True

    def is_multiplayer(self) -> bool:
        """Check if the game is in any multiplayer mode (local or VS AI)."""
        return self._is_local_multiplayer or self.is_vs_ai()

    def is_local_multiplayer(self) -> bool:
        """Check if the game is in local multiplayer mode."""
        return self._is_local_multiplayer

    def is_vs_ai(self) -> bool:
        """Check if the game is in vs. AI mode."""
        return self.ai_interface is not None

    def end_turn(self) -> None:
        """End the current player's turn and switch to the next player."""
        if not self.is_multiplayer() and not self.is_vs_ai():
            # In single player (not vs. AI), no need to switch players
            return

        if self.is_local_multiplayer():
            # In local multiplayer, switch players
            is_switching_to_player2 = self.current_player == 1

            # Toggle between player 1 and 2
            self.current_player = 3 - self.current_player

            # Ensure the player number in the game engine is also updated
            self.game.current_player = self.current_player

            # Increment turn counter when switching back to player 1
            if self.current_player == 1:
                self.game.turn += 1

            # Initialize the new player's turn (apply passive skills and reset flags)
            self.game.initialize_next_player_turn()

            # When switching to player 2, check if it's the first turn
            if is_switching_to_player2:
                if hasattr(self.game, 'is_player2_first_turn') and self.game.is_player2_first_turn:
                    self._apply_player2_first_turn_buff()
                    self.game.is_player2_first_turn = False

            logger.info(f"Switched to player {self.current_player}")

        elif self.is_vs_ai():
            # In VS AI mode, switch between player 1 and AI (player 2)
            if self.current_player == 1:
                # Player 1 ended turn, switch to AI (player 2)
                self.current_player = 2
                self.game.current_player = 2

                # Initialize the AI player's turn
                self.game.initialize_next_player_turn()

                # If this is player 2's first turn, apply move bonus to their units
                if hasattr(self.game, 'is_player2_first_turn') and self.game.is_player2_first_turn:
                    self._apply_player2_first_turn_buff()
                    self.game.is_player2_first_turn = False

                # Indicate player 2's turn has started
                message_log.add_system_message("Player 2's turn")

                # Process AI turn immediately
                logger.info("Processing AI turn")
                if self.ai_interface:
                    # Get UI reference from game if available
                    ui = getattr(self.game, 'ui', None)

                    # Process AI turn
                    message_log.add_system_message("AI is thinking...")
                    self.ai_interface.process_turn()

                    # Execute the AI's turn
                    logger.info("Executing AI's turn")
                    self.game.execute_turn(ui)

                    # Switch back to player 1 after AI turn
                    self.current_player = 1
                    self.game.current_player = 1

                    # Initialize player 1's turn (execute_turn already incremented turn counter)
                    self.game.initialize_next_player_turn()

                    message_log.add_system_message("Player 1's turn")

                    # Force UI refresh if UI is available
                    if ui and hasattr(ui, 'draw_board'):
                        ui.draw_board()
            else:
                # This shouldn't happen in VS AI mode, but handle it anyway
                self.current_player = 1
                self.game.current_player = 1
                self.game.initialize_next_player_turn()

    def _apply_player2_first_turn_buff(self) -> None:
        """Apply +1 move range buff to all player 2 units on their first turn."""
        from boneglaive.utils.message_log import message_log, MessageType

        # Find all player 2 units and apply the buff
        player2_units = [unit for unit in self.game.units if unit.player == 2 and unit.is_alive()]

        if player2_units:
            for unit in player2_units:
                # Check if unit is immune to status effects (GRAYMAN with Stasiality)
                if unit.is_immune_to_effects():
                    logger.debug(f"{unit.get_display_name()} is immune to first turn bonus due to Stasiality")
                    continue

                # Add the move bonus (+1)
                unit.move_range_bonus += 1
                unit.first_turn_move_bonus = True
                unit.first_turn_move_bonus_duration = 1

            message_log.add_message(
                "Player 2 units gain +1 movement range on their first turn",
                MessageType.SYSTEM
            )

    def get_current_player(self) -> int:
        """Get the current player number (1 or 2)."""
        if self._is_local_multiplayer or self.is_vs_ai():
            return self.current_player
        return 1

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.ai_interface:
            self.ai_interface.cleanup()
            self.ai_interface = None
        self.initialized = False
        logger.info("Multiplayer manager cleaned up")
