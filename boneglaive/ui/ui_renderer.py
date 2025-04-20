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
        """Draw the game board and UI with enhanced visuals.
        
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
        
        # Draw header with improved styling
        term_height, term_width = self.renderer.get_terminal_size()
        
        # Draw full-width header bar with improved styling
        for x in range(term_width):
            self.renderer.draw_text(0, x, " ", 15)  # Cyan background for header bar
        
        # Set header content based on game state
        if self.game_ui.game.setup_phase:
            # Setup phase header
            setup_player = self.game_ui.game.setup_player
            player_color = chat_component.player_colors.get(setup_player, 1)
            player_indicator = f"Player {setup_player}"
            
            # Show setup-specific header
            header = f"{player_indicator} | SETUP PHASE | Units left: {self.game_ui.game.setup_units_remaining[setup_player]}"
            
            if self.game_ui.game.setup_units_remaining[setup_player] == 0:
                header += " | Press 'y' to confirm"
                
            # Draw map name in header
            map_name = self.game_ui.game.map.name
            map_text = f"Map: {map_name}"
            self.renderer.draw_text(0, term_width - len(map_text) - 2, map_text, 15, curses.A_BOLD)
        else:
            # Normal game header
            current_player = self.game_ui.multiplayer.get_current_player()
            game_mode = "Single" if not self.game_ui.multiplayer.is_multiplayer() else "Local" if self.game_ui.multiplayer.is_local_multiplayer() else "LAN"
            
            # Get player color for the header
            player_color = chat_component.player_colors.get(current_player, 1)
            
            # Create shorter player indicator
            player_indicator = f"Player {current_player}"
            turn_text = f"Turn {self.game_ui.game.turn}"
            
            # Build the rest of the header
            header = f"{player_indicator} | {turn_text} | Mode: {mode_manager.mode.capitalize()} | Game: {game_mode}"
            if self.game_ui.multiplayer.is_network_multiplayer():  # Only show YOUR TURN/WAITING in network multiplayer
                status = "YOUR TURN" if self.game_ui.multiplayer.is_current_player_turn() else "WAITING"
                header += f" | {status}"
            
            # Draw map name and turn number in header
            map_name = self.game_ui.game.map.name
            map_text = f"Map: {map_name}"
            self.renderer.draw_text(0, term_width - len(map_text) - 2, map_text, 15, curses.A_BOLD)
        
        # Additional header indicators
        if chat_component.chat_mode:
            header += " | CHAT MODE"
            
        if debug_config.enabled:
            header += " | DEBUG"
        
        # Draw player indicator with player color and the rest with header styling
        player_text = f" {player_indicator} "
        self.renderer.draw_text(0, 1, player_text, 15, curses.A_BOLD)
        self.renderer.draw_text(0, len(player_text) + 1, header[len(player_indicator):], 15)
        
        # Draw frame around the game board
        # Top border
        self.renderer.draw_text(1, 0, "┌" + "─" * (WIDTH*2) + "┐", 16)
        
        # Side borders
        for y in range(HEIGHT):
            self.renderer.draw_text(y + 2, 0, "│", 16)
            self.renderer.draw_text(y + 2, WIDTH*2 + 1, "│", 16)
        
        # Bottom border
        self.renderer.draw_text(HEIGHT + 2, 0, "└" + "─" * (WIDTH*2) + "┘", 16)
        
        # Draw the battlefield with enhanced visuals
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
                
                # Start with normal attributes
                attributes = 0
                
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
                        attributes = curses.A_BOLD  # Always make units bold for better visibility
                        
                        # Add HP indicator for unit's health status
                        hp_percentage = unit.hp / unit.max_hp
                        if hp_percentage < 0.33:
                            # Low health - add blinking and red
                            attributes |= curses.A_DIM
                            color_id = 21  # Health color (red)
                        elif hp_percentage < 0.66:
                            # Medium health - add yellow
                            attributes |= curses.A_DIM
                            color_id = 22  # Attack color (yellow)
                        
                        # If this unit is being targeted for attack and attack targets should be shown
                        if attacking_unit and show_attack_targets:
                            # Check if cursor is here before drawing targeted unit
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                            
                            if is_cursor_here:
                                # Draw with cursor color but still bold to show it's selected
                                self.renderer.draw_tile(y, x, tile, 2, attributes | curses.A_BOLD)
                            else:
                                # Use red to show this unit is targeted for attack
                                self.renderer.draw_tile(y, x, tile, 10, attributes | curses.A_BOLD)
                            continue
                            
                        # If this is the selected unit and we should show selection, use special highlighting
                        if show_selection and cursor_manager.selected_unit and unit == cursor_manager.selected_unit:
                            # Check if cursor is also here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                            
                            if is_cursor_here:
                                # Draw with cursor color but bold to show it's selected
                                self.renderer.draw_tile(y, x, tile, 2, attributes | curses.A_BOLD)
                            else:
                                # Use highlighted color for selected unit
                                self.renderer.draw_tile(y, x, tile, 9, attributes | curses.A_BOLD)
                            continue
                            
                        # Check if cursor is here for normal unit draw
                        is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                        if is_cursor_here:
                            # Draw with cursor color
                            self.renderer.draw_tile(y, x, tile, 2, attributes)
                        else:
                            # Normal unit draw with attributes
                            self.renderer.draw_tile(y, x, tile, color_id, attributes)
                        continue
                
                elif target_unit and not unit:
                    # This is a move target location - draw a "ghost" of the moving unit
                    tile = self.game_ui.asset_manager.get_unit_tile(target_unit.type)
                    color_id = 8  # Gray preview color
                    attributes = curses.A_DIM
                    
                    # Check if it's selected (user selected the ghost)
                    is_selected = show_selection and cursor_manager.selected_unit and \
                                cursor_manager.selected_unit == target_unit and \
                                cursor_manager.selected_unit.move_target == (y, x)
                    
                    # Check if cursor is here
                    is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                    
                    if is_selected:
                        # Draw as selected ghost
                        self.renderer.draw_tile(y, x, tile, 9, attributes)
                        continue
                    elif is_cursor_here:
                        # Draw with cursor color
                        self.renderer.draw_tile(y, x, tile, 2, attributes)
                        continue
                    
                    # Otherwise draw normal ghost
                    self.renderer.draw_tile(y, x, tile, color_id, attributes)
                
                # Check if position is highlighted for movement or attack
                if pos in cursor_manager.highlighted_positions:
                    if mode_manager.mode == "move":
                        color_id = 5
                        tile = self.game_ui.asset_manager.get_ui_tile("move")
                        attributes = curses.A_BOLD
                    elif mode_manager.mode == "attack":
                        color_id = 6
                        tile = self.game_ui.asset_manager.get_ui_tile("target")
                        attributes = curses.A_BOLD
                
                # Cursor takes priority for visibility when it should be shown
                if show_cursor and pos == cursor_manager.cursor_pos:
                    # Override tile with cursor tile for better visibility
                    cursor_tile = self.game_ui.asset_manager.get_ui_tile("cursor")
                    
                    # Show cursor with different color if hovering over impassable terrain
                    if not self.game_ui.game.map.is_passable(y, x):
                        color_id = 6  # Red to indicate impassable
                    else:
                        color_id = 2  # Normal cursor color
                        
                    # Draw cursor with tile and attributes
                    self.renderer.draw_tile(y, x, cursor_tile, color_id, curses.A_BOLD)
                    continue
                
                # Draw the regular cell
                self.renderer.draw_tile(y, x, tile, color_id, attributes)
        
        # Draw status panel border - allocate space for stat panel to the right of the game board
        panel_start_x = WIDTH*2 + 2
        panel_width = 30  # Fixed width for panel
        
        # Top border
        self.renderer.draw_text(1, panel_start_x, "┌" + "─" * panel_width + "┐", 16)
        
        # Side borders - match height with game board
        for y in range(HEIGHT + 1):
            self.renderer.draw_text(y + 2, panel_start_x, "│", 16)
            self.renderer.draw_text(y + 2, panel_start_x + panel_width + 1, "│", 16)
        
        # Bottom border
        self.renderer.draw_text(HEIGHT + 2, panel_start_x, "└" + "─" * panel_width + "┘", 16)
        
        # Panel title
        panel_title = " STATUS PANEL "
        self.renderer.draw_text(1, panel_start_x + (panel_width - len(panel_title)) // 2, panel_title, 16, curses.A_BOLD)
        
        # Draw unit info in status panel if selected
        panel_content_x = panel_start_x + 2
        if cursor_manager.selected_unit:
            unit = cursor_manager.selected_unit
            
            # Unit name with player color
            unit_color = 3 if unit.player == 1 else 4
            unit_title = f"{unit.type.name.upper()} (Player {unit.player})"
            self.renderer.draw_text(3, panel_content_x, unit_title, unit_color, curses.A_BOLD)
            
            # Horizontal line
            self.renderer.draw_text(4, panel_content_x, "─" * (panel_width - 3), 16)
            
            # Stats with icons and colors
            health_icon = self.game_ui.asset_manager.get_ui_tile("health")
            attack_icon = self.game_ui.asset_manager.get_ui_tile("attack")
            move_icon = self.game_ui.asset_manager.get_ui_tile("move")
            
            # Health with colored bar
            health_text = f"{health_icon} Health: {unit.hp}/{unit.max_hp}"
            self.renderer.draw_text(6, panel_content_x, health_text, 21)
            
            # Health bar
            health_percent = unit.hp / unit.max_hp
            health_bar_width = 20
            filled_width = int(health_percent * health_bar_width)
            
            # Health bar background
            self.renderer.draw_text(7, panel_content_x, "░" * health_bar_width, 8)
            
            # Health bar fill - color based on health percentage
            bar_color = 21
            if health_percent > 0.66:
                bar_color = 24
            elif health_percent > 0.33:
                bar_color = 22
                
            if filled_width > 0:
                self.renderer.draw_text(7, panel_content_x, "█" * filled_width, bar_color, curses.A_BOLD)
            
            # Attack and defense
            attack_text = f"{attack_icon} Attack: {unit.attack}"
            defense_text = f"Defense: {unit.defense}"
            self.renderer.draw_text(9, panel_content_x, attack_text, 22)
            self.renderer.draw_text(10, panel_content_x, defense_text, 23)
            
            # Movement and range
            move_text = f"{move_icon} Move: {unit.move_range}"
            range_text = f"Range: {unit.attack_range}"
            self.renderer.draw_text(12, panel_content_x, move_text, 24)
            self.renderer.draw_text(13, panel_content_x, range_text, 25)
            
            # Status (move/attack targets)
            if unit.move_target:
                move_status = f"Movement planned: ({unit.move_target[0]}, {unit.move_target[1]})"
                self.renderer.draw_text(15, panel_content_x, move_status, 24)
                
            if unit.attack_target:
                attack_status = f"Attack planned: ({unit.attack_target[0]}, {unit.attack_target[1]})"
                self.renderer.draw_text(16, panel_content_x, attack_status, 21)
        else:
            # No unit selected - show game info
            self.renderer.draw_text(3, panel_content_x, "No Unit Selected", 16, curses.A_BOLD)
            
            # Game info
            game_mode = "Single Player"
            if self.game_ui.multiplayer.is_multiplayer():
                game_mode = "Local Multiplayer" if self.game_ui.multiplayer.is_local_multiplayer() else "LAN Multiplayer"
                
            # Display game info
            game_info = [
                f"Mode: {game_mode}",
                f"Map: {self.game_ui.game.map.name}",
                f"Turn: {self.game_ui.game.turn}",
                f"Current Phase: {mode_manager.mode.capitalize()}",
                f"Current Player: {self.game_ui.multiplayer.get_current_player()}"
            ]
            
            # Display each line
            for i, line in enumerate(game_info):
                self.renderer.draw_text(6 + i*2, panel_content_x, line, 16)
            
            # Controls reminder
            controls_title = "Controls Reminder"
            self.renderer.draw_text(16, panel_content_x, controls_title, 16, curses.A_BOLD)
            
            controls = [
                "Arrow keys/HJKL: Move cursor",
                "Enter/Space: Select",
                "Esc/c: Cancel",
                "?: Help screen",
                "Tab: Cycle units"
            ]
            
            for i, line in enumerate(controls):
                self.renderer.draw_text(18 + i, panel_content_x, line, 1)
                
        # Draw message log if enabled
        if message_log_component.show_log:
            message_log_component.draw_message_log()
            
        # Draw chat input field if in chat mode
        if chat_component.chat_mode:
            chat_component.draw_chat_input()
            
        # Draw action menu if a unit is selected
        if self.game_ui.action_menu_component.visible:
            self.game_ui.action_menu_component.draw()
        
        # Status bar at the bottom
        status_y = HEIGHT + 4
        # Draw status bar background
        for x in range(term_width):
            self.renderer.draw_text(status_y, x, " ", 20)
            
        # Current message in status bar
        if self.game_ui.message:
            self.renderer.draw_text(status_y, 2, self.game_ui.message, 20, curses.A_BOLD)
        
        # Help reminder on the right side of status bar
        help_text = "Press ? for help"
        self.renderer.draw_text(status_y, term_width - len(help_text) - 2, help_text, 20)
        
        # Draw winner info if game is over
        if self.game_ui.game.winner:
            # Create a victory announcement box
            win_y = HEIGHT // 2 - 2
            win_x = WIDTH - 7
            
            # Draw box
            self.renderer.draw_text(win_y, win_x, "┌" + "─" * 14 + "┐", 17)
            self.renderer.draw_text(win_y+1, win_x, "│              │", 17)
            self.renderer.draw_text(win_y+2, win_x, "│   VICTORY!   │", 17)
            self.renderer.draw_text(win_y+3, win_x, "│              │", 17)
            self.renderer.draw_text(win_y+4, win_x, "└" + "─" * 14 + "┘", 17)
            
            # Draw winner text with player color
            winner_color = 3 if self.game_ui.game.winner == 1 else 4
            winner_text = f"Player {self.game_ui.game.winner} Wins!"
            self.renderer.draw_text(win_y+2, win_x + (16 - len(winner_text)) // 2, winner_text, winner_color, curses.A_BOLD)
        
        # Draw debug overlay if enabled
        if debug_config.show_debug_overlay:
            try:
                # Get debug information
                overlay_lines = debug_config.get_debug_overlay()
                
                # Add game state info
                game_state = self.game_ui.game.get_game_state()
                overlay_lines.append(f"Game State: Turn {game_state['turn']}, Player {game_state['current_player']}")
                overlay_lines.append(f"Units: {len(game_state['units'])}")
                
                # Display overlay at top right
                overlay_x = term_width - 30
                for i, line in enumerate(overlay_lines):
                    self.renderer.draw_text(i + 2, overlay_x, line, 1, curses.A_DIM)
            except Exception as e:
                # Never let debug features crash the game
                logger.error(f"Error displaying debug overlay: {str(e)}")
        
        self.renderer.refresh()