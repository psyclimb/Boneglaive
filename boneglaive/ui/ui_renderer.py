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
        
        # Draw header with improved formatting
        header_y = 0
        
        # Clear the header line first
        self.renderer.draw_text(header_y, 0, " " * self.renderer.width, 1)
        
        if self.game_ui.game.setup_phase:
            # Setup phase header
            setup_player = self.game_ui.game.setup_player
            player_color = chat_component.player_colors.get(setup_player, 1)
            
            # Draw player indicator with box drawing chars
            player_text = f"■ PLAYER {setup_player} ■"
            self.renderer.draw_text(header_y, 2, player_text, player_color, curses.A_BOLD)
            
            # Draw setup phase info
            setup_text = "SETUP PHASE"
            self.renderer.draw_text(header_y, len(player_text) + 4, setup_text, 1, curses.A_BOLD)
            
            # Draw units remaining
            units_left = self.game_ui.game.setup_units_remaining[setup_player]
            units_text = f"UNITS LEFT: {units_left}"
            self.renderer.draw_text(header_y, len(player_text) + len(setup_text) + 6, units_text, 1)
            
            # Add confirmation indicator if all units placed
            if units_left == 0:
                confirm_text = "PRESS 'Y' TO CONFIRM"
                self.renderer.draw_text(header_y, len(player_text) + len(setup_text) + len(units_text) + 8, confirm_text, 1, curses.A_BOLD)
        else:
            # Normal game header
            current_player = self.game_ui.multiplayer.get_current_player()
            player_color = chat_component.player_colors.get(current_player, 1)
            
            # Draw player indicator with box drawing chars 
            player_text = f"■ PLAYER {current_player} ■"
            self.renderer.draw_text(header_y, 2, player_text, player_color, curses.A_BOLD)
            
            # Draw action mode (select/move/attack)
            mode_text = f"MODE: {mode_manager.mode.upper()}"
            self.renderer.draw_text(header_y, len(player_text) + 4, mode_text, 1)
            
            # Draw multiplayer info
            game_mode = "SINGLE" if not self.game_ui.multiplayer.is_multiplayer() else "LOCAL" if self.game_ui.multiplayer.is_local_multiplayer() else "LAN"
            game_text = f"GAME: {game_mode}"
            self.renderer.draw_text(header_y, len(player_text) + len(mode_text) + 6, game_text, 1)
            
            # Add turn indicator for network play
            if self.game_ui.multiplayer.is_network_multiplayer():
                turn_text = "YOUR TURN" if self.game_ui.multiplayer.is_current_player_turn() else "WAITING"
                self.renderer.draw_text(header_y, len(player_text) + len(mode_text) + len(game_text) + 8, turn_text, 1, curses.A_BOLD)
        
        # Add chat mode indicator if active
        if chat_component.chat_mode:
            chat_text = "CHAT MODE"
            self.renderer.draw_text(header_y, self.renderer.width - len(chat_text) - 2, chat_text, 1, curses.A_BOLD)
            
        # Add debug indicator if enabled
        if debug_config.enabled:
            debug_text = "DEBUG"
            # Position at far right if chat is not active
            x_pos = self.renderer.width - len(debug_text) - 2
            if chat_component.chat_mode:
                # Position before chat indicator
                chat_text = "CHAT MODE"
                x_pos = self.renderer.width - len(chat_text) - len(debug_text) - 4
            self.renderer.draw_text(header_y, x_pos, debug_text, 1, curses.A_BOLD)
        
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
                        
                # Check if any unit is targeting this position for a skill
                skill_targeting_unit = None
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.skill_target == (y, x) and u.selected_skill:
                        skill_targeting_unit = u
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
                            
                        # If this unit is being targeted for a skill and attack targets should be shown
                        # (reusing the show_attack_targets flag for skills too)
                        if skill_targeting_unit and show_attack_targets:
                            # Check if cursor is here before drawing targeted unit
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                            
                            if is_cursor_here:
                                # Draw with cursor color but still bold to show it's selected
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Use blue background to show this unit is targeted for a skill (different from attack)
                                self.renderer.draw_tile(y, x, tile, 15, curses.A_BOLD)  # 15 for blue skill target
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
                
                # Check if position is highlighted for movement, attack, or skill
                if pos in cursor_manager.highlighted_positions:
                    if mode_manager.mode == "move":
                        color_id = 5  # Green for movement
                    elif mode_manager.mode == "attack":
                        color_id = 6  # Red for attack
                    elif mode_manager.mode == "skill":
                        color_id = 16  # Blue for skill targeting
                
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
        
        # Draw unit info with improved formatting
        info_line = HEIGHT+1
        
        # Clear the unit info line
        self.renderer.draw_text(info_line, 0, " " * self.renderer.width, 1)
        
        if cursor_manager.selected_unit:
            unit = cursor_manager.selected_unit
            
            # Draw unit type with player color
            player_color = 3 if unit.player == 1 else 4
            type_info = f"▶ UNIT: {unit.type.name} ◀"
            self.renderer.draw_text(info_line, 2, type_info, player_color, curses.A_BOLD)
            
            # Draw HP with color based on health percentage
            hp_percent = unit.hp / unit.max_hp
            hp_color = 2  # default green
            if hp_percent <= 0.3:
                hp_color = 6  # red for critical
            elif hp_percent <= 0.7:
                hp_color = 7  # yellow for damaged
                
            hp_info = f"HP: {unit.hp}/{unit.max_hp}"
            self.renderer.draw_text(info_line, len(type_info) + 4, hp_info, hp_color)
            
            # Draw combat stats
            combat_info = f"ATK: {unit.attack} | DEF: {unit.defense}"
            self.renderer.draw_text(info_line, len(type_info) + len(hp_info) + 6, combat_info, 1)
            
            # Draw movement stats
            effective_stats = unit.get_effective_stats()
            effective_move = effective_stats['move_range']
            effective_attack = effective_stats['attack_range']
            
            # Split the movement and range display so we can color only MOVE red when penalized
            move_part = f"MOVE: {effective_move}"
            range_part = f"RANGE: {effective_attack}"
            
            # Calculate position for each part
            move_pos = len(type_info) + len(hp_info) + len(combat_info) + 8
            range_pos = move_pos + len(move_part) + 3  # +3 for the " | " separator
            
            # Determine if there's a movement penalty for display purposes
            move_color = 1  # Default color
            move_attr = 0   # Default attribute
            if unit.move_range_bonus < 0:
                # Show negative MOVE bonus in red to indicate penalty
                move_color = 6  # Red for penalty
                move_attr = curses.A_BOLD  # Make it bold for emphasis
            
            # Draw MOVE part with appropriate color
            self.renderer.draw_text(info_line, move_pos, move_part, move_color, move_attr)
            
            # Draw separator
            self.renderer.draw_text(info_line, move_pos + len(move_part), " | ", 1)
            
            # Draw RANGE part with normal color (always)
            self.renderer.draw_text(info_line, range_pos, range_part, 1)
        
        # Draw message with better visibility
        msg_line = HEIGHT+2
        self.renderer.draw_text(msg_line, 0, " " * self.renderer.width, 1)  # Clear line
        if self.game_ui.message:
            msg_indicator = ">> "
            self.renderer.draw_text(msg_line, 2, msg_indicator, 1, curses.A_BOLD)
            self.renderer.draw_text(msg_line, 2 + len(msg_indicator), self.game_ui.message, 1)
        
        # Draw simplified help reminder and controls
        help_line = HEIGHT+3
        self.renderer.draw_text(help_line, 0, " " * self.renderer.width, 1)  # Clear line
        help_text = "Press ? for help | [M]ove | [A]ttack | [E]nd Turn"
        self.renderer.draw_text(help_line, 2, help_text, 1)
        
        # Draw winner info if game is over
        if self.game_ui.game.winner:
            winner_line = HEIGHT+4
            self.renderer.draw_text(winner_line, 0, " " * self.renderer.width, 1)  # Clear line
            winner_color = 3 if self.game_ui.game.winner == 1 else 4
            winner_text = f"★★★ PLAYER {self.game_ui.game.winner} WINS! ★★★"
            # Center the winner text
            center_pos = (self.renderer.width - len(winner_text)) // 2
            self.renderer.draw_text(winner_line, center_pos, winner_text, winner_color, curses.A_BOLD)
        
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