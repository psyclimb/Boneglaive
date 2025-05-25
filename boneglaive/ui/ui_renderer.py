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
    def _draw_spinner_in_menu_area(self):
        """Draw the spinner animation in the action menu area during action resolution."""
        # Calculate menu position (same as in ActionMenuComponent)
        menu_x = WIDTH * 2 + 2
        menu_y = 2
        
        # Set dimensions for the spinner menu
        menu_width = 25
        menu_height = 6  # Smaller than regular menu
        
        # Draw menu border
        # Top border
        self.renderer.draw_text(menu_y, menu_x, "┌" + "─" * (menu_width - 2) + "┐", 1)
        
        # Side borders
        for i in range(1, menu_height - 1):
            self.renderer.draw_text(menu_y + i, menu_x, "│", 1)
            self.renderer.draw_text(menu_y + i, menu_x + menu_width - 1, "│", 1)
        
        # Bottom border
        self.renderer.draw_text(menu_y + menu_height - 1, menu_x, "└" + "─" * (menu_width - 2) + "┘", 1)
        
        # Draw header
        header_text = " RESOLVING "
        header_x = menu_x + (menu_width - len(header_text)) // 2
        self.renderer.draw_text(menu_y + 1, header_x, header_text, 3, curses.A_BOLD)
        
        # Draw separator
        self.renderer.draw_text(menu_y + 2, menu_x + 1, "─" * (menu_width - 2), 1)
        
        # Draw spinner
        spinner_char = self.game_ui.spinner_chars[self.game_ui.spinner_frame]
        spinner_line = f"       {spinner_char}       "
        spinner_x = menu_x + (menu_width - len(spinner_line)) // 2
        self.renderer.draw_text(menu_y + 4, spinner_x, spinner_line, 3, curses.A_BOLD)
    
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
        
        # Draw header with improved formatting - keeping it compact
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
            
        # Spinner is now drawn in the action menu area instead of the header
        
        # Draw the battlefield
        for y in range(HEIGHT):
            for x in range(WIDTH):
                pos = Position(y, x)
                
                # Get terrain at this position
                terrain = self.game_ui.game.map.get_terrain_at(y, x)
                
                # Map terrain type to tile representation, color, and attribute
                tile_attr = 0  # Default: no special attributes

                # Save the position for later use
                pos_tuple = (y, x)

                # Flag to track if we have a teleport anchor here (for later)
                has_teleport_anchor = False
                if hasattr(self.game_ui.game, 'teleport_anchors') and pos_tuple in self.game_ui.game.teleport_anchors:
                    anchor = self.game_ui.game.teleport_anchors[pos_tuple]
                    # Check if this anchor is active and marked as imbued
                    if anchor.get('active', False) and anchor.get('imbued', False):
                        has_teleport_anchor = True

                # Check if this position is inside a Marrow Dike interior first (priority rendering)
                pos_tuple = (y, x)
                if hasattr(self.game_ui.game, 'marrow_dike_interior') and pos_tuple in self.game_ui.game.marrow_dike_interior:
                    dike_info = self.game_ui.game.marrow_dike_interior[pos_tuple]
                    # If this is an upgraded Marrow Dike, show blood plasma
                    if dike_info.get('upgraded', False):
                        tile = "~"  # Blood plasma appearance
                        color_id = 20  # Red color for blood
                    else:
                        # Non-upgraded interior still shows as regular floor
                        tile = self.game_ui.asset_manager.get_terrain_tile("empty")
                        color_id = 1  # Default color
                # Handle regular terrain types
                elif terrain == TerrainType.EMPTY:
                    tile = self.game_ui.asset_manager.get_terrain_tile("empty")
                    color_id = 1  # Default color
                            
                elif terrain == TerrainType.LIMESTONE:
                    tile = self.game_ui.asset_manager.get_terrain_tile("limestone")
                    color_id = 12  # White for limestone
                    tile_attr = curses.A_BOLD  # Bright white via bold attribute
                elif terrain == TerrainType.DUST:
                    tile = self.game_ui.asset_manager.get_terrain_tile("dust")
                    color_id = 11  # Normal white for dust
                elif terrain == TerrainType.PILLAR:
                    tile = self.game_ui.asset_manager.get_terrain_tile("pillar")
                    color_id = 13  # White for pillars
                # Different furniture types
                elif terrain == TerrainType.FURNITURE:
                    tile = self.game_ui.asset_manager.get_terrain_tile("furniture")
                    color_id = 14  # White for furniture
                    tile_attr = curses.A_DIM  # Dim white/gray via dim attribute

                    # Override if this has a teleport anchor
                    if has_teleport_anchor:
                        tile = "¤"  # Replace with currency symbol
                        color_id = 3  # Yellow color for imbued furniture
                        tile_attr = curses.A_BOLD  # Make it bold

                elif terrain == TerrainType.COAT_RACK:
                    tile = self.game_ui.asset_manager.get_terrain_tile("coat_rack")
                    color_id = 14  # White for furniture
                    tile_attr = curses.A_DIM  # Dim white/gray via dim attribute

                    # Override if this has a teleport anchor
                    if has_teleport_anchor:
                        tile = "¤"  # Replace with currency symbol
                        color_id = 3  # Yellow color for imbued furniture
                        tile_attr = curses.A_BOLD  # Make it bold

                elif terrain == TerrainType.OTTOMAN:
                    tile = self.game_ui.asset_manager.get_terrain_tile("ottoman")
                    color_id = 14  # White for furniture
                    tile_attr = curses.A_DIM  # Dim white/gray via dim attribute

                    # Override if this has a teleport anchor
                    if has_teleport_anchor:
                        tile = "¤"  # Replace with currency symbol
                        color_id = 3  # Yellow color for imbued furniture
                        tile_attr = curses.A_BOLD  # Make it bold

                elif terrain == TerrainType.CONSOLE:
                    tile = self.game_ui.asset_manager.get_terrain_tile("console")
                    color_id = 14  # White for furniture
                    tile_attr = curses.A_DIM  # Dim white/gray via dim attribute

                    # Override if this has a teleport anchor
                    if has_teleport_anchor:
                        tile = "¤"  # Replace with currency symbol
                        color_id = 3  # Yellow color for imbued furniture
                        tile_attr = curses.A_BOLD  # Make it bold

                elif terrain == TerrainType.DEC_TABLE:
                    tile = self.game_ui.asset_manager.get_terrain_tile("dec_table")
                    color_id = 14  # White for furniture
                    tile_attr = curses.A_DIM  # Dim white/gray via dim attribute

                    # Override if this has a teleport anchor
                    if has_teleport_anchor:
                        tile = "¤"  # Replace with currency symbol
                        color_id = 3  # Yellow color for imbued furniture
                        tile_attr = curses.A_BOLD  # Make it bold

                elif terrain == TerrainType.MARROW_WALL:
                    tile = self.game_ui.asset_manager.get_terrain_tile("marrow_wall")
                    
                    # Check if we have owner information for this wall to determine player color
                    if hasattr(self.game_ui.game, 'marrow_dike_tiles'):
                        pos_tuple = (y, x)
                        if pos_tuple in self.game_ui.game.marrow_dike_tiles:
                            wall_info = self.game_ui.game.marrow_dike_tiles[pos_tuple]
                            # Use owner's player color if available
                            if 'owner' in wall_info and wall_info['owner']:
                                color_id = 3 if wall_info['owner'].player == 1 else 4  # Player's color
                            else:
                                color_id = 20  # Default red for Marrow Wall if no owner info
                        else:
                            color_id = 20  # Default red for Marrow Wall if not in tracked tiles
                    else:
                        color_id = 20  # Default red for Marrow Wall if no tracking dictionary
                elif terrain == TerrainType.RAIL:
                    tile = self.game_ui.asset_manager.get_terrain_tile("rail")
                    color_id = 6  # Yellow color for rails
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
                        
                        # Check if this is a HEINOUS_VAPOR and use its specific symbol if available
                        if unit.type == UnitType.HEINOUS_VAPOR and hasattr(unit, 'vapor_symbol') and unit.vapor_symbol:
                            tile = unit.vapor_symbol
                        
                        # Check if this is a charging FOWL_CONTRIVANCE
                        if unit.type == UnitType.FOWL_CONTRIVANCE and hasattr(unit, 'charging_status') and unit.charging_status:
                            tile = "≡"  # Charging symbol
                            color_id = 6  # Yellow color for charging
                        
                        # No special symbol for GRAYMAN skills
                        # (Previously showed | for Græ Exchange, but this was removed)
                            
                        # Check for echo units (priority over estranged)
                        if hasattr(unit, 'is_echo') and unit.is_echo:
                            # Use lowercase psi (ψ) symbol to show it's an echo of GRAYMAN's Ψ
                            tile = f"ψ"
                            # Use dim attribute for echo units to make them appear faint
                            attributes = curses.A_DIM
                        # Check for estranged units
                        elif hasattr(unit, 'estranged') and unit.estranged:
                            # Add a tilde character to show the unit has estranged status effect
                            enhanced_tile = f"{tile}~"  # Combine unit symbol with tilde (represents phasing)
                            # Save this for later use in the status effect checks
                        
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
                            # Check if unit is trapped by a MANDIBLE FOREMAN's Viceroy ability
                            is_trapped = unit.trapped_by is not None
                            
                            if is_trapped:
                                # Combine the unit symbol with a mandible symbol but keep original color
                                enhanced_tile = f"{tile}Ξ"  # Combine unit symbol with mandible symbol
                                # Use the unit's original color instead of changing to yellow
                                self.renderer.draw_tile(y, x, enhanced_tile, color_id, curses.A_BOLD)
                                
                                # Also add a mandible symbol below the unit to reinforce the trap visual
                                trap_y = min(y + 1, HEIGHT - 1)  # Ensure we don't go off the bottom
                                trap_x = x
                                # Only draw if position is empty and within bounds
                                if trap_y < HEIGHT and not self.game_ui.game.get_unit_at(trap_y, trap_x):
                                    trap_symbol = "Ξ"  # Mandible symbol
                                    jaw_color = 7  # Keep jaw symbol yellow
                                    self.renderer.draw_tile(trap_y, trap_x, trap_symbol, jaw_color, curses.A_BOLD)
                            # Check if unit has Site Inspection status effect
                            elif hasattr(unit, 'status_site_inspection') and unit.status_site_inspection:
                                # Add an eye symbol to show the unit has Site Inspection status effect
                                enhanced_tile = f"{tile}Θ"  # Combine unit symbol with the Greek theta eye
                                # Use green color to indicate positive status effect
                                self.renderer.draw_tile(y, x, enhanced_tile, color_id, curses.A_BOLD)
                            # Check if unit is affected by Ossify status effect
                            elif hasattr(unit, 'ossify_active') and unit.ossify_active:
                                # Add an O symbol to show the unit has Ossify status effect 
                                enhanced_tile = f"{tile}O"  # Combine unit symbol with O for Ossify
                                # Use green color to indicate positive status effect
                                self.renderer.draw_tile(y, x, enhanced_tile, color_id, curses.A_BOLD)
                            # Check if unit is affected by Bone Tithe defensive buff
                            elif hasattr(unit, 'slough_def_duration') and unit.slough_def_duration > 0:
                                # Add an asterisk symbol to show the unit has marrow coating from Bone Tithe
                                enhanced_tile = f"{tile}*"  # Combine unit symbol with * for marrow coating
                                # Use green color to indicate positive status effect
                                self.renderer.draw_tile(y, x, enhanced_tile, color_id, curses.A_BOLD)
                            # Check if unit is affected by Jawline status effect
                            elif hasattr(unit, 'jawline_affected') and unit.jawline_affected:
                                # Add uppercase Xi symbol to show the unit has Jawline status effect
                                enhanced_tile = f"{tile}Ξ"  # Combine unit symbol with uppercase Xi (resembles mechanical jaws)
                                # Use red color with dim attribute to indicate negative status effect
                                self.renderer.draw_tile(y, x, enhanced_tile, color_id, curses.A_DIM)
                            # Check if unit has embedded shrapnel from Fragcrest
                            elif hasattr(unit, 'shrapnel_duration') and unit.shrapnel_duration > 0:
                                # Add x symbol to show embedded shrapnel status effect
                                enhanced_tile = f"{tile}x"  # Combine unit symbol with x (represents embedded fragments)
                                # Use red color with dim attribute to indicate ongoing damage
                                self.renderer.draw_tile(y, x, enhanced_tile, 1, curses.A_DIM)
                            # Check if unit is affected by Pry movement penalty
                            elif (hasattr(unit, 'pry_duration') and unit.pry_duration > 0) or (hasattr(unit, 'pry_active') and unit.pry_active) or (unit.was_pried and unit.move_range_bonus < 0):
                                # Add a slash to show movement reduction from Pry
                                enhanced_tile = f"{tile}/"  # Combine unit symbol with slash (represents glaive that pried)
                                # Retain the unit's original color instead of changing to red
                                self.renderer.draw_tile(y, x, enhanced_tile, color_id, 0)  # Original color without special attributes
                            # Check if unit is affected by estranged status effect
                            elif hasattr(unit, 'estranged') and unit.estranged:
                                # Add tilde symbol to show the unit has estranged status effect
                                enhanced_tile = f"{tile}~"  # Combine unit symbol with tilde (represents phasing)
                                # Use gray color (19) to indicate phasing out of spacetime
                                self.renderer.draw_tile(y, x, enhanced_tile, 19, curses.A_DIM)
                            # Check if unit has Market Futures investment effect
                            elif hasattr(unit, 'has_investment_effect') and unit.has_investment_effect:
                                # Add pound sign symbol to show investment status
                                enhanced_tile = f"{tile}£"  # Combine unit symbol with pound sign (represents investment)
                                # Use bright gold/yellow color (3) to indicate investment
                                self.renderer.draw_tile(y, x, enhanced_tile, 3, curses.A_BOLD)
                            # Check if unit is affected by Auction Curse DOT
                            elif hasattr(unit, 'auction_curse_dot') and unit.auction_curse_dot:
                                # Add cent sign symbol to show auction curse status
                                enhanced_tile = f"{tile}¢"  # Combine unit symbol with cent sign (representing cursed money)
                                # Use red color to indicate negative status effect
                                self.renderer.draw_tile(y, x, enhanced_tile, 6, curses.A_BOLD)
                            # Check if unit has first-turn move bonus
                            elif hasattr(unit, 'first_turn_move_bonus') and unit.first_turn_move_bonus:
                                # Add plus symbol to show movement bonus
                                enhanced_tile = f"{tile}+"  # Combine unit symbol with plus (represents extra movement)
                                # Use bright green color to indicate positive status effect
                                self.renderer.draw_tile(y, x, enhanced_tile, 3, curses.A_BOLD)
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
                
                # Check if this position is a vault target indicator
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Vault" and u.vault_target_indicator == (y, x):
                        # This position is a vault target - draw an indicator
                        tile = self.game_ui.asset_manager.get_ui_tile("vault_target")
                        color_id = 3 if u.player == 1 else 4  # Color based on player
                        
                        # Check if cursor is here
                        is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                        
                        if is_cursor_here:
                            # Draw with cursor color 
                            self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                        else:
                            # Draw the vault target indicator
                            self.renderer.draw_tile(y, x, tile, color_id, curses.A_BOLD)
                        continue
                
                # Check if this position is in an Expedite path indicator
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Expedite" and hasattr(u, 'expedite_path_indicator') and \
                       u.expedite_path_indicator is not None and (y, x) in u.expedite_path_indicator:
                        # This position is part of an Expedite path - draw direction indicator
                        # Get index in path to determine how to visualize it
                        path_index = u.expedite_path_indicator.index((y, x))
                        path_length = len(u.expedite_path_indicator)
                        
                        # Different visualization for different parts of the path
                        if path_index == path_length - 1:  # End position (destination)
                            tile = "→"  # Arrow pointing forward for final position
                        else:
                            # For intermediate positions, show a subtle path indicator
                            tile = "·"  # Dot for intermediate positions
                        
                        color_id = 3 if u.player == 1 else 4  # Color based on player
                        
                        # Check if cursor is here
                        is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                        
                        if is_cursor_here:
                            # Draw with cursor color
                            self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                        else:
                            # Draw the expedite path indicator - only make the end bold
                            attrs = curses.A_BOLD if path_index == path_length - 1 else 0
                            self.renderer.draw_tile(y, x, tile, color_id, attrs)
                        continue
                
                # Check if this position is a teleport target indicator
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       (u.selected_skill.name == "Teleport" or 
                        u.selected_skill.name == "Delta Config" or 
                        u.selected_skill.name == "Græ Exchange") and \
                       hasattr(u, 'teleport_target_indicator') and u.teleport_target_indicator == (y, x):
                        
                        # Different visualization based on skill type
                        if u.selected_skill.name == "Græ Exchange":
                            # For Grae Exchange, show a gray Ψ
                            tile = "Ψ"
                            color_id = 8  # Gray color
                        else:
                            # For other teleport skills, use the standard indicator
                            tile = self.game_ui.asset_manager.get_ui_tile("teleport_target")
                            color_id = 3 if u.player == 1 else 4  # Color based on player
                        
                        # Check if cursor is here
                        is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                        
                        if is_cursor_here:
                            # Draw with cursor color 
                            self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                        else:
                            # Draw the teleport target indicator - use dim for Grae Exchange
                            attrs = curses.A_DIM if u.selected_skill.name == "Græ Exchange" else curses.A_BOLD
                            self.renderer.draw_tile(y, x, tile, color_id, attrs)
                        continue
                        
                # Check if this position is a Site Inspection target indicator or within its area
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.site_inspection_indicator is not None:
                        target_y, target_x = u.site_inspection_indicator
                        
                        # Check if this position is within the 3x3 area of Site Inspection
                        in_area = (abs(y - target_y) <= 1 and abs(x - target_x) <= 1)
                        
                        if in_area:
                            # Determine what to draw
                            if (y, x) == (target_y, target_x):
                                # Center of inspection area - use full square
                                tile = self.game_ui.asset_manager.get_ui_tile("site_inspection")
                            else:
                                # Edge of inspection area - use a dotted border
                                tile = "·"
                            
                            color_id = 3 if u.player == 1 else 4  # Color based on player
                            
                            # Check if cursor is here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                            
                            if is_cursor_here:
                                # Draw with cursor color 
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Draw the site inspection indicator - lighter attribute for area
                                attr = curses.A_BOLD if (y, x) == (target_y, target_x) else 0
                                # Use the center square for the target and dots for the surrounding area
                                self.renderer.draw_tile(y, x, tile, color_id, attr)
                            continue
                            
                # Check if this position is in a Jawline network area
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Jawline" and u.jawline_indicator is not None:
                        target_y, target_x = u.jawline_indicator

                        # Check if this position is within the 3x3 area of Jawline
                        in_area = (abs(y - target_y) <= 1 and abs(x - target_x) <= 1)
                        # Skip center (that's the user's position)
                        if (y, x) == (target_y, target_x):
                            continue

                        if in_area:
                            # Draw jawline indicator - use mandible symbol for surrounding tiles
                            tile = "Ξ"  # Mandible symbol for jawline network
                            color_id = 3 if u.player == 1 else 4  # Color based on player

                            # Check if cursor is here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)

                            if is_cursor_here:
                                # Draw with cursor color
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Draw the jawline indicator
                                self.renderer.draw_tile(y, x, tile, color_id, 0)
                            continue


                # Check if this position is in a FOWL_CONTRIVANCE skill targeting indicator
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name'):
                        
                        # Big Arc AOE indicator
                        if u.selected_skill.name == "Big Arc" and hasattr(u, 'big_arc_indicator') and u.big_arc_indicator is not None:
                            target_y, target_x = u.big_arc_indicator
                            # Check if this position is within the 3x3 area
                            in_area = (abs(y - target_y) <= 1 and abs(x - target_x) <= 1)
                            if in_area:
                                tile = "*" if (y, x) == (target_y, target_x) else "·"
                                color_id = 3 if u.player == 1 else 4
                                
                        # Gaussian Dusk charging indicator
                        elif u.selected_skill.name == "Gaussian Dusk" and hasattr(u, 'gaussian_dusk_indicator') and u.gaussian_dusk_indicator is not None:
                            # Show charging indicator at user position
                            if (y, x) == (u.y, u.x):
                                tile = "≡"  # Charging symbol
                                color_id = 3 if u.player == 1 else 4
                                
                        # Fragcrest cone indicator
                        elif u.selected_skill.name == "Fragcrest" and hasattr(u, 'fragcrest_indicator') and u.fragcrest_indicator is not None:
                            # Show targeting indicator (would need cone calculation for full effect)
                            target_y, target_x = u.fragcrest_indicator
                            if (y, x) == (target_y, target_x):
                                tile = "X"  # Target marker
                                color_id = 3 if u.player == 1 else 4

                        # Check if cursor is here
                        is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)

                        if is_cursor_here:
                            # Draw with cursor color
                            self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                        else:
                            # Draw the skill indicator
                            attr = curses.A_BOLD
                            self.renderer.draw_tile(y, x, tile, color_id, attr)
                            continue

                # Check if this position is a Broaching Gas target
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Broaching Gas" and u.broaching_gas_indicator is not None:
                        target_y, target_x = u.broaching_gas_indicator

                        if (y, x) == (target_y, target_x):
                            # Draw broaching gas indicator
                            tile = "Φ"  # Phi symbol for Broaching Gas
                            color_id = 3 if u.player == 1 else 4  # Color based on player

                            # Check if cursor is here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)

                            if is_cursor_here:
                                # Draw with cursor color
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Draw the broaching gas indicator
                                self.renderer.draw_tile(y, x, tile, color_id, curses.A_BOLD)
                            continue

                # Check if this position is a Saft-E-Gas target
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Saft-E-Gas" and u.saft_e_gas_indicator is not None:
                        target_y, target_x = u.saft_e_gas_indicator

                        if (y, x) == (target_y, target_x):
                            # Draw saft-e-gas indicator
                            tile = "Θ"  # Theta symbol for Safety Gas
                            color_id = 3 if u.player == 1 else 4  # Color based on player

                            # Check if cursor is here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)

                            if is_cursor_here:
                                # Draw with cursor color
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Draw the saft-e-gas indicator
                                self.renderer.draw_tile(y, x, tile, color_id, curses.A_BOLD)
                            continue

                # Check if this position has a unit targeted by Diverge skill
                # Since Diverge can target either a vapor or the GAS_MACHINIST itself,
                # we need to check if any unit's skill_target matches this position
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Diverge" and u.skill_target is not None:
                        # If there's a unit at this position and it's the target of Diverge
                        if (y, x) == u.skill_target:
                            # Get the unit at this position
                            target_unit = self.game_ui.game.get_unit_at(y, x)

                            # Only highlight if there's actually a unit here
                            if target_unit:
                                # Use the unit's existing tile, but add a highlight effect
                                tile = self.game_ui.asset_manager.get_unit_tile(target_unit.type)

                                # If it's a vapor, use its custom symbol
                                if target_unit.type == UnitType.HEINOUS_VAPOR and hasattr(target_unit, 'vapor_symbol') and target_unit.vapor_symbol:
                                    tile = target_unit.vapor_symbol

                                # Draw the unit tile with a highlighted attribute
                                unit_color = 3 if target_unit.player == 1 else 4  # Base color on unit's player

                                # Cursor takes priority
                                is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                                if is_cursor_here:
                                    self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                                else:
                                    # Use reverse video to create the highlight effect
                                    self.renderer.draw_tile(y, x, tile, unit_color, curses.A_REVERSE)
                                continue

                # Check if this position is a Market Futures target
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Market Futures" and u.market_futures_indicator is not None:
                        target_y, target_x = u.market_futures_indicator

                        if (y, x) == (target_y, target_x):
                            # Draw market futures indicator
                            tile = "$"  # Dollar sign for furniture evaluation
                            color_id = 3 if u.player == 1 else 4  # Color based on player

                            # Check if cursor is here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)

                            if is_cursor_here:
                                # Draw with cursor color
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Draw the market futures indicator
                                self.renderer.draw_tile(y, x, tile, color_id, curses.A_BOLD)
                            continue

                # Check if this position is a Divine Depreciation target
                for u in self.game_ui.game.units:
                    if u.is_alive() and u.selected_skill and hasattr(u.selected_skill, 'name') and \
                       u.selected_skill.name == "Divine Depreciation" and u.divine_depreciation_indicator is not None:
                        target_y, target_x = u.divine_depreciation_indicator

                        # Check if this position is within the 5x5 area of Divine Depreciation
                        in_area = (abs(y - target_y) <= 2 and abs(x - target_x) <= 2)

                        if in_area:
                            # Draw divine depreciation indicator
                            if (y, x) == (target_y, target_x):
                                # Center of depreciation area - use down arrow symbol
                                tile = "↓"  # Down arrow for value depreciation
                            else:
                                # Edge of depreciation area - use a dotted border
                                tile = "·"  # Dots for surrounding area

                            color_id = 3 if u.player == 1 else 4  # Color based on player

                            # Check if cursor is here
                            is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)

                            if is_cursor_here:
                                # Draw with cursor color
                                self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                            else:
                                # Draw the divine depreciation indicator
                                attr = curses.A_BOLD if (y, x) == (target_y, target_x) else 0
                                self.renderer.draw_tile(y, x, tile, color_id, attr)
                            continue

                # Check if this position is an Auction Curse enemy target
                for u in self.game_ui.game.units:
                    if u.is_alive() and hasattr(u, 'auction_curse_enemy_indicator') and u.auction_curse_enemy_indicator is not None:
                        target_y, target_x = u.auction_curse_enemy_indicator

                        if (y, x) == (target_y, target_x):
                            # Get the unit at this position
                            target_unit = self.game_ui.game.get_unit_at(y, x)

                            if target_unit:
                                # Use the unit's existing tile, but add a highlight effect
                                tile = self.game_ui.asset_manager.get_unit_tile(target_unit.type)

                                # Draw the unit tile with a highlighted attribute
                                unit_color = 3 if target_unit.player == 1 else 4  # Base color on unit's player

                                # Cursor takes priority
                                is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                                if is_cursor_here:
                                    self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                                else:
                                    # Use reverse video to show enemy target
                                    self.renderer.draw_tile(y, x, tile, 1, curses.A_REVERSE)  # Red reverse for enemy
                                continue

                # Check if this position is an Auction Curse ally target
                for u in self.game_ui.game.units:
                    if u.is_alive() and hasattr(u, 'auction_curse_ally_indicator') and u.auction_curse_ally_indicator is not None:
                        target_y, target_x = u.auction_curse_ally_indicator

                        if (y, x) == (target_y, target_x):
                            # Get the unit at this position
                            target_unit = self.game_ui.game.get_unit_at(y, x)

                            if target_unit:
                                # Use the unit's existing tile, but add a highlight effect
                                tile = self.game_ui.asset_manager.get_unit_tile(target_unit.type)

                                # Draw the unit tile with a highlighted attribute
                                unit_color = 3 if target_unit.player == 1 else 4  # Base color on unit's player

                                # Cursor takes priority
                                is_cursor_here = (pos == cursor_manager.cursor_pos and show_cursor)
                                if is_cursor_here:
                                    self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)
                                else:
                                    # Use green for ally target
                                    self.renderer.draw_tile(y, x, tile, 2, curses.A_BOLD)  # Green bold for ally
                                continue

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
                
                # Draw the cell with the tile attribute
                self.renderer.draw_tile(y, x, tile, color_id, tile_attr)
                
        # Draw message log if enabled
        if message_log_component.show_log:
            message_log_component.draw_message_log()
            
        # Draw chat input field if in chat mode
        if chat_component.chat_mode:
            chat_component.draw_chat_input()
            
        # Always show spinner during resolving phase, otherwise show action menu if visible
        if self.game_ui.spinner_active:
            # Always draw the spinner in the action menu area during resolving
            self._draw_spinner_in_menu_area()
        elif self.game_ui.action_menu_component.visible:
            # Draw action menu if visible and not in resolving phase
            self.game_ui.action_menu_component.draw()
        
        # Draw unit info with improved formatting
        # Add +2 to ensure a blank line between map and info
        info_line = HEIGHT+2
        
        # Clear the unit info line
        self.renderer.draw_text(info_line, 0, " " * self.renderer.width, 1)
        
        if cursor_manager.selected_unit:
            unit = cursor_manager.selected_unit
            
            # Draw unit type with player color
            player_color = 3 if unit.player == 1 else 4
            type_info = f"▶ UNIT: {unit.get_display_name()} ◀"
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
            
            # Draw combat stats with effective values that include bonuses
            effective_stats = unit.get_effective_stats()
            effective_attack = effective_stats['attack']
            effective_defense = effective_stats['defense']
            
            # Show bonuses in the display if they exist
            attack_display = f"{effective_attack}"
            if unit.attack_bonus != 0:
                attack_display = f"{unit.attack}+{unit.attack_bonus}" if unit.attack_bonus > 0 else f"{unit.attack}{unit.attack_bonus}"
                
            defense_display = f"{effective_defense}"
            if unit.defense_bonus != 0:
                defense_display = f"{unit.defense}+{unit.defense_bonus}" if unit.defense_bonus > 0 else f"{unit.defense}{unit.defense_bonus}"
            
            # Split combat stats for individual coloring
            atk_text = f"ATK: {attack_display}"
            def_text = f" | DEF: {defense_display}"
            
            # Determine colors based on bonuses and Estrange effect
            atk_color = 2 if unit.attack_bonus > 0 else (6 if unit.attack_bonus < 0 or (hasattr(unit, 'estranged') and unit.estranged) else 1)  # Green for bonus, red for penalty or if estranged
            def_color = 2 if unit.defense_bonus > 0 else (6 if unit.defense_bonus < 0 or (hasattr(unit, 'estranged') and unit.estranged) else 1)  # Green for bonus, red for penalty or if estranged
            
            # Draw with appropriate coloring
            pos = len(type_info) + len(hp_info) + 6
            self.renderer.draw_text(info_line, pos, atk_text, atk_color)
            self.renderer.draw_text(info_line, pos + len(atk_text), def_text, def_color)
            
            # Draw movement stats
            effective_stats = unit.get_effective_stats()
            effective_move = effective_stats['move_range']
            effective_attack = effective_stats['attack_range']
            
            # Split the movement and range display so we can color only MOVE red when penalized
            # Check for first turn movement bonus
            if hasattr(unit, 'first_turn_move_bonus') and unit.first_turn_move_bonus:
                move_part = f"MOVE: {effective_move}+"  # Add + to show boost
                move_color = 3  # Green color for the boost
            elif unit.move_range_bonus < 0:
                move_part = f"MOVE: {effective_move}"
                move_color = 1  # Red for penalty
            else:
                move_part = f"MOVE: {effective_move}"
                move_color = 7  # Normal color

            range_part = f"RANGE: {effective_attack}"
            
            # Add a separator between DEF and MOVE stats
            stats_separator = " | "
            
            # Calculate position for each part - use the combined length of atk_text and def_text + separator
            move_pos = len(type_info) + len(hp_info) + len(atk_text) + len(def_text) + len(stats_separator) + 6
            
            # Draw the separator between DEF and MOVE
            sep_pos = len(type_info) + len(hp_info) + len(atk_text) + len(def_text) + 6
            self.renderer.draw_text(info_line, sep_pos, stats_separator, 1)
            range_pos = move_pos + len(move_part) + 3  # +3 for the " | " separator
            
            # Determine if there's a movement penalty, bonus, or Estrange for display purposes
            move_color = 1  # Default color
            move_attr = 0   # Default attribute

            # Check for first turn movement bonus - highest priority
            if hasattr(unit, 'first_turn_move_bonus') and unit.first_turn_move_bonus:
                # Show the first turn bonus with a different color without the + symbol
                move_part = f"MOVE: {effective_move}"  # No + symbol, just use color to show the boost
                move_color = 3  # Green color for the boost
                move_attr = curses.A_BOLD  # Make it bold for emphasis
            # Regular penalties or Estrange effect
            elif unit.move_range_bonus < 0 or (hasattr(unit, 'estranged') and unit.estranged):
                # Show negative MOVE bonus in red to indicate penalty
                move_color = 6  # Red for penalty
                move_attr = curses.A_BOLD  # Make it bold for emphasis
            # Other movement bonuses
            elif unit.move_range_bonus > 0:
                # Show positive MOVE bonus in green
                move_color = 2  # Green for bonus
            
            # Determine range color based on estranged status
            range_color = 1  # Default color
            range_attr = 0   # Default attribute
            if hasattr(unit, 'estranged') and unit.estranged:
                # Show RANGE in red if affected by Estrange
                range_color = 6  # Red for penalty
                range_attr = curses.A_BOLD  # Make it bold for emphasis
            elif unit.attack_range_bonus > 0:
                # Show positive RANGE bonus in green
                range_color = 2  # Green for bonus
            elif unit.attack_range_bonus < 0:
                # Show negative RANGE bonus in red
                range_color = 6  # Red for penalty
                range_attr = curses.A_BOLD  # Make it bold for emphasis
            
            # Draw MOVE part with appropriate color
            self.renderer.draw_text(info_line, move_pos, move_part, move_color, move_attr)
            
            # Draw separator
            self.renderer.draw_text(info_line, move_pos + len(move_part), " | ", 1)
            
            # Draw RANGE part with appropriate color
            self.renderer.draw_text(info_line, range_pos, range_part, range_color, range_attr)
            
            # Draw status effects on a new line
            status_line = info_line + 1
            positive_effects = []
            negative_effects = []
            
            # Duration-based effects (categorized as positive or negative)
            if hasattr(unit, 'shrapnel_duration') and unit.shrapnel_duration > 0:
                negative_effects.append(f"Shrapnel({unit.shrapnel_duration})")
            if hasattr(unit, 'auction_curse_dot') and unit.auction_curse_dot:
                duration = getattr(unit, 'auction_curse_dot_duration', '?')
                negative_effects.append(f"Auction Curse({duration})")
            if hasattr(unit, 'echo_duration') and unit.echo_duration > 0:
                positive_effects.append(f"Echo({unit.echo_duration})")
            if hasattr(unit, 'vapor_duration') and unit.vapor_duration > 0 and unit.type == UnitType.HEINOUS_VAPOR:
                vapor_type = getattr(unit, 'vapor_type', 'Vapor')
                positive_effects.append(f"{vapor_type}({unit.vapor_duration})")
            if hasattr(unit, 'slough_def_duration') and unit.slough_def_duration > 0:
                positive_effects.append(f"Slough Defense({unit.slough_def_duration})")
            
            # Boolean status effects (categorized as positive or negative)
            if hasattr(unit, 'jawline_affected') and unit.jawline_affected:
                # Check if it has duration, otherwise just show boolean
                if hasattr(unit, 'jawline_duration') and unit.jawline_duration > 0:
                    negative_effects.append(f"Jawline({unit.jawline_duration})")
                else:
                    negative_effects.append("Jawline")
            if hasattr(unit, 'estranged') and unit.estranged:
                negative_effects.append("Estranged")
            if hasattr(unit, 'has_investment_effect') and unit.has_investment_effect:
                positive_effects.append("Investment")
            if hasattr(unit, 'charging_status') and unit.charging_status:
                positive_effects.append("Charging")
            if hasattr(unit, 'ossify_active') and unit.ossify_active:
                positive_effects.append("Ossify")
            if hasattr(unit, 'status_site_inspection') and unit.status_site_inspection:
                positive_effects.append("Site Inspection")
            if hasattr(unit, 'first_turn_move_bonus') and unit.first_turn_move_bonus:
                positive_effects.append("First Turn Bonus")
            if hasattr(unit, 'is_echo') and unit.is_echo and not (hasattr(unit, 'echo_duration') and unit.echo_duration > 0):
                # Only show if not already shown with duration
                positive_effects.append("Echo")
            if hasattr(unit, 'is_invulnerable') and unit.is_invulnerable:
                positive_effects.append("Invulnerable")
            if hasattr(unit, 'diverge_return_position') and unit.diverge_return_position:
                positive_effects.append("Diverge Return")
            
            # Movement/action penalties and traps (negative)
            if hasattr(unit, 'was_pried') and unit.was_pried and unit.move_range_bonus < 0:
                negative_effects.append("Pried")
            if hasattr(unit, 'trapped_by') and unit.trapped_by is not None:
                # Check if it has duration, otherwise just show boolean
                if hasattr(unit, 'trap_duration') and unit.trap_duration > 0:
                    negative_effects.append(f"Trapped({unit.trap_duration})")
                else:
                    negative_effects.append("Trapped")
            
            # Display status effects if any exist
            if positive_effects or negative_effects:
                # Start with "Status: " label
                self.renderer.draw_text(status_line, 2, "Status: ", 7)  # White for label
                current_pos = 2 + len("Status: ")
                
                # Draw positive effects in green
                if positive_effects:
                    positive_text = ", ".join(positive_effects)
                    self.renderer.draw_text(status_line, current_pos, positive_text, 3)  # Green color (COLOR_GREEN on COLOR_BLACK)
                    current_pos += len(positive_text)
                    
                    # Add separator if both positive and negative exist
                    if negative_effects:
                        self.renderer.draw_text(status_line, current_pos, ", ", 1)  # White separator
                        current_pos += 2
                
                # Draw negative effects in red
                if negative_effects:
                    negative_text = ", ".join(negative_effects)
                    self.renderer.draw_text(status_line, current_pos, negative_text, 20)  # Red color (COLOR_RED on COLOR_BLACK)
        
        # Draw message with better visibility
        msg_line = HEIGHT+4  # Moved down by 1 to make room for status line
        self.renderer.draw_text(msg_line, 0, " " * self.renderer.width, 1)  # Clear line

        # Check if we should display cosmic value
        cursor_pos = self.game_ui.cursor_manager.cursor_pos
        current_player = self.game_ui.multiplayer.get_current_player()

        # Check if cursor is on furniture
        if self.game_ui.game.map.is_furniture(cursor_pos.y, cursor_pos.x):
            # Get cosmic value if player has DELPHIC_APPRAISER
            cosmic_value = self.game_ui.game.map.get_cosmic_value(
                cursor_pos.y, cursor_pos.x,
                player=current_player,
                game=self.game_ui.game
            )

            # Display cosmic value if available
            if cosmic_value is not None:
                value_message = f"Furniture cosmic value: {cosmic_value}"
                # Only show value message if there's no other message
                if not self.game_ui.message:
                    msg_indicator = ">> "
                    self.renderer.draw_text(msg_line, 2, msg_indicator, 1, curses.A_BOLD)
                    self.renderer.draw_text(msg_line, 2 + len(msg_indicator), value_message, 1)

        # Display regular message if available
        if self.game_ui.message:
            msg_indicator = ">> "
            self.renderer.draw_text(msg_line, 2, msg_indicator, 1, curses.A_BOLD)
            self.renderer.draw_text(msg_line, 2 + len(msg_indicator), self.game_ui.message, 1)
        
        # Draw simplified help reminder and controls
        help_line = HEIGHT+5
        self.renderer.draw_text(help_line, 0, " " * self.renderer.width, 1)  # Clear line

        # Draw game over prompt if visible
        if hasattr(self.game_ui, 'game_over_prompt') and self.game_ui.game_over_prompt.visible:
            self.game_ui.game_over_prompt.draw()
        
        # Check if the selected unit is affected by Jawline
        cursor_manager = self.game_ui.cursor_manager
        unit_immobilized = (cursor_manager.selected_unit and 
                          hasattr(cursor_manager.selected_unit, 'jawline_affected') and 
                          cursor_manager.selected_unit.jawline_affected)
        
        # Different help text based on whether unit is immobilized
        if unit_immobilized:
            # Only show help text
            help_text = "Press ? for help"
            self.renderer.draw_text(help_line, 2, help_text, 1)
        else:
            # Normal controls display - simplified to just help text
            help_text = "Press ? for help"
            self.renderer.draw_text(help_line, 2, help_text, 1)
        
        # Draw winner info if game is over
        if self.game_ui.game.winner:
            winner_line = HEIGHT+5
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
                line_offset = HEIGHT + 6 + message_log_component.log_height + 2
                for i, line in enumerate(overlay_lines):
                    self.renderer.draw_text(line_offset + i, 0, line, 1, curses.A_DIM)
            except Exception as e:
                # Never let debug features crash the game
                logger.error(f"Error displaying debug overlay: {str(e)}")
        
        self.renderer.refresh()