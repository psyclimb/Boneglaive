#!/usr/bin/env python3
import curses
from typing import Optional, List, Tuple, Dict

from boneglaive.utils.constants import HEIGHT, WIDTH, UnitType
from boneglaive.game.engine import Game
from boneglaive.game.map import TerrainType
from boneglaive.utils.coordinates import Position
from boneglaive.utils.debug import debug_config, measure_perf, logger

class UIRenderer:
    """Component for managing UI rendering."""
    
    def __init__(self, renderer, game_ui):
        self.renderer = renderer
        self.game_ui = game_ui
    
    @measure_perf
    def draw_board(self, show_cursor=True, show_selection=True, show_attack_targets=True):
        """Draw the game board and UI.
        
        Args:
            show_cursor: Whether to show the cursor (default: True)
            show_selection: Whether to show selected unit highlighting (default: True)
            show_attack_targets: Whether to show attack target highlighting (default: True)
        """
        # Get component references for cleaner code
        cursor_manager = self.game_ui.cursor_manager
        mode_manager = self.game_ui.mode_manager
        message_log_component = self.game_ui.message_log_component
        help_component = self.game_ui.help_component
        chat_component = self.game_ui.chat_component
        
        # Set cursor visibility
        self.renderer.set_cursor(False)  # Always hide the physical cursor
        
        # Clear screen
        self.renderer.clear_screen()
        
        # If help screen is being shown, draw it and return
        if help_component.show_help:
            help_component.draw_help_screen()
            self.renderer.refresh()
            return
            
        # If log history screen is being shown, draw it and return
        if message_log_component.show_log_history:
            message_log_component.draw_log_history_screen()
            self.renderer.refresh()
            return
            
        # If setup instructions are being shown, draw them and return
        if self.game_ui.game.setup_phase and mode_manager.show_setup_instructions:
            mode_manager.draw_setup_instructions()
            self.renderer.refresh()
            return
        
        # Draw header
        if self.game_ui.game.setup_phase:
            # Setup phase header
            setup_player = self.game_ui.game.setup_player
            player_color = chat_component.player_colors.get(setup_player, 1)
            player_indicator = f"Player {setup_player}"
            
            # Show setup-specific header
            header = f"{player_indicator} | SETUP PHASE | Units left: {self.game_ui.game.setup_units_remaining[setup_player]}"
            
            if self.game_ui.game.setup_units_remaining[setup_player] == 0:
                header += " | Press 'y' to confirm"
        else:
            # Normal game header
            current_player = self.game_ui.multiplayer.get_current_player()
            game_mode = "Single" if not self.game_ui.multiplayer.is_multiplayer() else "Local" if self.game_ui.multiplayer.is_local_multiplayer() else "LAN"
            
            # Get player color for the header
            player_color = chat_component.player_colors.get(current_player, 1)
            
            # Create shorter player indicator
            player_indicator = f"Player {current_player}"
            
            # Build the rest of the header
            header = f"{player_indicator} | Mode: {mode_manager.mode} | Game: {game_mode}"
            if self.game_ui.multiplayer.is_network_multiplayer():  # Only show YOUR TURN/WAITING in network multiplayer
                header += f" | {'YOUR TURN' if self.game_ui.multiplayer.is_current_player_turn() else 'WAITING'}"
        
        # Additional header indicators
        if chat_component.chat_mode:
            header += " | CHAT MODE"
            
        if debug_config.enabled:
            header += " | DEBUG ON"
        
        # Draw player indicator with player color and the rest with default color
        self.renderer.draw_text(0, 0, player_indicator, player_color, curses.A_BOLD)
        self.renderer.draw_text(0, len(player_indicator), header[len(player_indicator):], 1)
        
        # Draw the battlefield
        for y in range(HEIGHT):
            for x in range(WIDTH):
                pos = Position(y, x)
                
                # Get terrain at this position
                terrain = self.game_ui.game.map.get_terrain_at(y, x)
                
                # Map terrain type to tile representation and color
                if terrain == TerrainType.EMPTY:
                    tile = self.game_ui.asset_manager.get_terrain_tile("empty")
                    color_id = 1  # Default color
                elif terrain == TerrainType.LIMESTONE:
                    tile = self.game_ui.asset_manager.get_terrain_tile("limestone")
                    color_id = 12  # Yellow for limestone
                elif terrain == TerrainType.DUST:
                    tile = self.game_ui.asset_manager.get_terrain_tile("dust")
                    color_id = 11  # Light white for dust
                elif terrain == TerrainType.PILLAR:
                    tile = self.game_ui.asset_manager.get_terrain_tile("pillar")
                    color_id = 13  # Magenta for pillars
                elif terrain == TerrainType.FURNITURE:
                    tile = self.game_ui.asset_manager.get_terrain_tile("furniture")
                    color_id = 14  # Cyan for furniture
                else:
                    # Fallback for any new terrain types
                    tile = self.game_ui.asset_manager.get_terrain_tile("empty")
                    color_id = 1  # Default color
                
                # Check if there's a unit at this position
                unit = self.game_ui.game.get_unit_at(y, x)
                
                # Check if any unit has a move target set to this position
                target_unit = None
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.move_target == (y, x):
                        target_unit = u
                        break
                        
                # Check if any unit is targeting this position for attack
                attacking_unit = None
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.attack_target == (y, x):
                        attacking_unit = u
                        break
                
                if unit:
                    # Check if this unit should be hidden during setup
                    hide_unit = (self.game_ui.game.setup_phase and 
                                self.game_ui.game.setup_player == 2 and 
                                unit.player == 1)
                                
                    # Even if unit is hidden, still draw cursor if it's here
                    if hide_unit and pos == cursor_manager.cursor_pos and show_cursor:
                        self.renderer.draw_tile(y, x, self.game_ui.asset_manager.get_terrain_tile("empty"), 2)
                        continue
                                
                    if not hide_unit:
                        # There's a real unit here
                        tile = self.game_ui.asset_manager.get_unit_tile(unit.type)
                        color_id = 3 if unit.player == 1 else 4
                        
                        # If this unit is being targeted for attack and attack targets should be shown
                        if attacking_unit and show_attack_targets:
                            # Check if cursor is here before drawing targeted unit
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                            
                            if is_cursor_here:
                                # Draw with cursor color but still bold to show it's selected
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Use red background to show this unit is targeted for attack
                                self.renderer.draw_tile(y, x, tile, 10, curses.A_BOLD)
                            continue
                            
                        # If this is the selected unit and we should show selection, use special highlighting
                        if show_selection and cursor_manager.selected_unit and unit == cursor_manager.selected_unit:
                            # Check if cursor is also here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                            
                            if is_cursor_here:
                                # Draw with cursor color but bold to show it's selected
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Use yellow background to highlight the selected unit
                                self.renderer.draw_tile(y, x, tile, 9, curses.A_BOLD)
                            continue
                            
                        # Check if cursor is here for normal unit draw
                        is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                        if is_cursor_here:
                            # Draw with cursor color
                            self.renderer.draw_tile(y, x, tile, 2)
                        else:
                            # Normal unit draw
                            self.renderer.draw_tile(y, x, tile, color_id)
                        continue
                
                elif target_unit and not unit:
                    # This is a move target location - draw a "ghost" of the moving unit
                    tile = self.game_ui.asset_manager.get_unit_tile(target_unit.type)
                    color_id = 8  # Gray preview color
                    
                    # Check if it's selected (user selected the ghost)
                    is_selected = show_selection and cursor_manager.selected_unit and \
                                cursor_manager.selected_unit == target_unit and \
                                cursor_manager.selected_unit.move_target == (y, x)
                    
                    # Check if cursor is here
                    is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                    
                    if is_selected:
                        # Draw as selected ghost (yellow background)
                        self.renderer.draw_tile(y, x, tile, 9, curses.A_DIM)
                        continue
                    elif is_cursor_here:
                        # Draw with cursor color
                        self.renderer.draw_tile(y, x, tile, 2)
                        continue
                    
                    # Otherwise draw normal ghost
                    self.renderer.draw_tile(y, x, tile, color_id, curses.A_DIM)
                
                # Check if position is highlighted for movement or attack
                if pos in cursor_manager.highlighted_positions:
                    if mode_manager.mode == "move":
                        color_id = 5
                    elif mode_manager.mode == "attack":
                        color_id = 6
                
                # Cursor takes priority for visibility when it should be shown
                if show_cursor and pos == cursor_manager.cursor_pos:
                    # Show cursor with different color if hovering over impassable terrain
                    if not self.game_ui.game.map.is_passable(y, x):
                        color_id = 6  # Red background to indicate impassable
                    else:
                        color_id = 2  # Normal cursor color
                
                # Draw the cell
                self.renderer.draw_tile(y, x, tile, color_id)
                
        # Draw message log if enabled
        if message_log_component.show_log:
            message_log_component.draw_message_log()
            
        # Draw chat input field if in chat mode
        if chat_component.chat_mode:
            chat_component.draw_chat_input()
            
        # Draw action menu if a unit is selected
        if self.game_ui.action_menu_component.visible:
            self.game_ui.action_menu_component.draw()
        
        # Draw unit info
        if cursor_manager.selected_unit:
            unit = cursor_manager.selected_unit
            unit_info = f"Selected: {unit.type.name} | HP: {unit.hp}/{unit.max_hp} | " \
                        f"ATK: {unit.attack} | DEF: {unit.defense} | " \
                        f"Move: {unit.move_range} | Range: {unit.attack_range}"
            self.renderer.draw_text(HEIGHT+1, 0, unit_info)
        
        # Draw message
        self.renderer.draw_text(HEIGHT+2, 0, self.game_ui.message)
        
        # Draw simplified help reminder
        help_text = "Press ? for help"
        self.renderer.draw_text(HEIGHT+3, 0, help_text)
        
        # Draw winner info if game is over
        if self.game_ui.game.winner:
            self.renderer.draw_text(HEIGHT+4, 0, f"Player {self.game_ui.game.winner} wins!", curses.A_BOLD)
        
        # Draw debug overlay if enabled
        if debug_config.show_debug_overlay:
            try:
                # Get debug information
                overlay_lines = debug_config.get_debug_overlay()
                
                # Add game state info
                game_state = self.game_ui.game.get_game_state()
                overlay_lines.append(f"Game State: Turn {game_state['turn']}, Player {game_state['current_player']}")
                overlay_lines.append(f"Units: {len(game_state['units'])}")
                
                # Display overlay below message log
                line_offset = HEIGHT + 5 + message_log_component.log_height + 2
                for i, line in enumerate(overlay_lines):
                    self.renderer.draw_text(line_offset + i, 0, line, 1, curses.A_DIM)
            except Exception as e:
                # Never let debug features crash the game
                logger.error(f"Error displaying debug overlay: {str(e)}")
        
        self.renderer.refresh()