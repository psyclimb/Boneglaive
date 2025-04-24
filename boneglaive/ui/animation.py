#!/usr/bin/env python3
import curses
import time

from boneglaive.utils.constants import UnitType
from boneglaive.utils.coordinates import Position, get_line
from boneglaive.utils.debug import measure_perf
from boneglaive.ui.components.base import UIComponent

class AnimationComponent(UIComponent):
    """Component for handling animations."""
    
    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        
    @measure_perf
    def show_attack_animation(self, attacker, target):
        """Show a visual animation for attacks."""
        # Get attack effect from asset manager
        effect_tile = self.game_ui.asset_manager.get_attack_effect(attacker.type)
        
        # Get animation sequence
        animation_sequence = self.game_ui.asset_manager.get_attack_animation_sequence(attacker.type)
        
        # Create start and end positions
        start_pos = Position(attacker.y, attacker.x)
        end_pos = Position(target.y, target.x)
        
        # For ranged attacks (archer and mage), show animation at origin then projectile path
        if attacker.type in [UnitType.ARCHER, UnitType.MAGE]:
            # First show attack preparation at attacker's position
            prep_sequence = animation_sequence[:2]  # First few frames of animation sequence
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x,
                prep_sequence,
                7,  # color ID
                0.2  # quick preparation animation
            )
            
            # Then animate projectile from attacker to target
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                effect_tile,
                7,  # color ID
                0.3  # duration
            )
        # For MANDIBLE_FOREMAN, show a special animation sequence for mandible jaws
        elif attacker.type == UnitType.MANDIBLE_FOREMAN:
            # Show the jaws animation at the attacker's position
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence[:3],  # First three frames - jaws opening
                7,  # color ID
                0.3  # slightly faster animation
            )
            
            # Show a short connecting animation between attacker and target
            # to visualize the mandibles reaching out
            self.renderer.animate_projectile(
                (start_pos.y, start_pos.x),
                (end_pos.y, end_pos.x),
                'Ξ',  # Mandible symbol
                7,    # color ID
                0.2   # quick connection
            )
            
            # Show the final part of the animation at the target position
            self.renderer.animate_attack_sequence(
                end_pos.y, end_pos.x, 
                animation_sequence[3:],  # Last frames - jaws clamping and retracting
                7,  # color ID
                0.4  # duration
            )
        # For GLAIVEMAN attacks, check range and choose the right animation
        elif attacker.type == UnitType.GLAIVEMAN:
            # Calculate distance to target
            distance = self.game_ui.game.chess_distance(start_pos.y, start_pos.x, end_pos.y, end_pos.x)
            
            # For range 2 attacks, use extended animation
            if distance == 2:
                # Get the extended animation sequence
                extended_sequence = self.game_ui.asset_manager.animation_sequences.get('glaiveman_extended_attack', [])
                if extended_sequence:
                    # First show windup animation at attacker's position
                    self.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        extended_sequence[:4],  # First few frames at attacker position
                        7,  # color ID
                        0.3  # duration
                    )
                    
                    # Then animate the glaive extending from attacker to target
                    # Calculate direction from attacker to target
                    path = get_line(start_pos, end_pos)
                    
                    # Get the middle position for the extending animation (if path has at least 3 points)
                    if len(path) >= 3:
                        mid_pos = path[1]  # Second point in the path
                        
                        # Show glaive extending through middle position
                        extension_chars = extended_sequence[4:8]  # Middle frames show extension
                        for i, char in enumerate(extension_chars):
                            self.renderer.draw_tile(mid_pos.y, mid_pos.x, char, 7)
                            self.renderer.refresh()
                            time.sleep(0.1)
                    
                    # Finally show the impact at target position
                    self.renderer.animate_attack_sequence(
                        end_pos.y, end_pos.x, 
                        extended_sequence[8:],  # Last frames at target position
                        7,  # color ID
                        0.3  # duration
                    )
                else:
                    # Fallback to standard animation if extended sequence isn't available
                    self.renderer.animate_attack_sequence(
                        start_pos.y, start_pos.x, 
                        animation_sequence,
                        7,  # color ID
                        0.5  # duration
                    )
            else:
                # For range 1 attacks, use standard animation
                self.renderer.animate_attack_sequence(
                    start_pos.y, start_pos.x, 
                    animation_sequence,
                    7,  # color ID
                    0.5  # duration
                )
        # For all other melee attacks, show standard animation
        else:
            # Show the attack animation at the attacker's position
            self.renderer.animate_attack_sequence(
                start_pos.y, start_pos.x, 
                animation_sequence,
                7,  # color ID
                0.5  # duration
            )
        
        # Show impact animation at target position with appropriate ASCII characters based on unit type
        if attacker.type == UnitType.MAGE:
            impact_animation = ['!', '*', '!']  # Magic impact
        elif attacker.type == UnitType.MANDIBLE_FOREMAN:
            impact_animation = ['>', '<', '}', '{', '≡']  # Mandible crushing impact
        else:
            impact_animation = ['+', 'x', '+']  # Standard melee/arrow impact
            
        impact_colors = [7] * len(impact_animation)
        impact_durations = [0.05] * len(impact_animation)
        
        # Use renderer's animate_attack_sequence for impact
        self.renderer.animate_attack_sequence(
            target.y, target.x,
            impact_animation,
            7,  # color ID 
            0.25  # duration
        )
        
        # Flash the target to show it was hit
        tile_ids = [self.game_ui.asset_manager.get_unit_tile(target.type)] * 4
        color_ids = [6 if target.player == 1 else 5, 3 if target.player == 1 else 4] * 2
        durations = [0.1] * 4
        
        # Use renderer's flash tile method
        self.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Show damage number above target with improved visualization
        # Use effective stats for correct damage display
        effective_attack = attacker.get_effective_stats()['attack']
        effective_defense = target.get_effective_stats()['defense']
        damage = max(1, effective_attack - effective_defense)
        damage_text = f"-{damage}"
        
        # Make damage text more prominent
        for i in range(3):
            # First clear the area
            self.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
            # Draw with alternating bold/normal for a flashing effect
            attrs = curses.A_BOLD if i % 2 == 0 else 0
            self.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
            self.renderer.refresh()
            time.sleep(0.1)
            
        # Final damage display (stays on screen slightly longer)
        self.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, curses.A_BOLD)
        self.renderer.refresh()
        time.sleep(0.3)
        
        # Redraw board to clear effects (without cursor, selection, or attack target highlighting)
        self.game_ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)