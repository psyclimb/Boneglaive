#!/usr/bin/env python3
"""
Skills specific to the GRAYMAN unit type.
This module contains all passive and active abilities for GRAYMAN units.
"""

from typing import Optional, TYPE_CHECKING

from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType
from boneglaive.utils.message_log import message_log, MessageType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class Stasiality(PassiveSkill):
    """Passive skill for GRAYMAN. Immune to status effects and displacement."""
    
    def __init__(self):
        super().__init__(
            name="Stasiality",
            key="S",
            description="Cannot have stats changed or be displaced. Immune to buffs, debuffs, forced movement, and terrain effects."
        )
    
    def apply_passive(self, user: 'Unit', game=None) -> None:
        # Implementation handled in Unit.is_immune_to_effects()
        pass


class DeltaConfigSkill(ActiveSkill):
    """Active skill for GRAYMAN. Teleports to any unoccupied tile on the map."""
    
    def __init__(self):
        super().__init__(
            name="Delta Config",
            key="D",
            description="Teleport to any unoccupied tile on the map.",
            target_type=TargetType.AREA,
            cooldown=12,
            range_=99
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Target position must be valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Target position must be passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        # Target position must be empty (no unit)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # Check if any other unit is already planning to teleport to this position
        # (via Vault, Delta Config, Grae Exchange, or any other teleport skill)
        for other_unit in game.units:
            if (other_unit.is_alive() and other_unit != user):
                # Check for vault targets
                if (hasattr(other_unit, 'vault_target_indicator') and
                    other_unit.vault_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set teleport target indicator for UI
        user.teleport_target_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} prepares to shift to Delta Config ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Delta Config teleportation skill."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        
        # Clear the teleport target indicator after execution
        user.teleport_target_indicator = None
        
        # Store original position for animations
        original_pos = (user.y, user.x)
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} initiates Delta Config!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get teleport out animation sequence
            teleport_out = ui.asset_manager.get_skill_animation_sequence('teleport_out')
            if not teleport_out:
                teleport_out = ['Ψ', '░', '▒', '▓', ' ']  # Fallback
                
            # Get teleport in animation sequence
            teleport_in = ui.asset_manager.get_skill_animation_sequence('teleport_in')
            if not teleport_in:
                teleport_in = [' ', '▓', '▒', '░', 'Ψ']  # Fallback
                
            # Play teleport out animation at original position
            ui.renderer.animate_attack_sequence(
                original_pos[0], original_pos[1],
                teleport_out,
                7,  # white color
                0.15  # duration
            )
            
            # Remove the unit temporarily to show it's gone
            temp_y, temp_x = user.y, user.x
            user.y, user.x = -999, -999  # Move off-screen
            
            # Redraw board to show unit is gone
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                
            # Brief pause for effect
            sleep_with_animation_speed(0.3)
            
            # Brief pre-teleport effect at destination
            # Just a single flash to indicate where teleport will occur
            ui.renderer.draw_tile(target_pos[0], target_pos[1], '*', 6)  # yellowish color star
            ui.renderer.refresh()
            sleep_with_animation_speed(0.1)
            
            # Play teleport in animation at target position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                teleport_in,
                7,  # white color
                0.15  # duration
            )
            
            # Actually move the unit to the target position
            user.y, user.x = target_pos
            
            # Redraw board after animations
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                
            # Flash the unit to emphasize teleport completed
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [6, 3 if user.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        else:
            # No UI, just set position without animations
            user.y, user.x = target_pos
        
        # Log the completion of teleportation
        message_log.add_message(
            f"{user.get_display_name()} teleports to position ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True


class EstrangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Phases a target out of normal spacetime."""
    
    def __init__(self):
        super().__init__(
            name="Estrange",
            key="E",
            description="Fire a beam that phases target out of normal spacetime. Target receives -1 to all actions.",
            target_type=TargetType.ENEMY,
            cooldown=3,
            range_=5
        )
        self.damage = 3  # Increased from 2 to 3
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False
            
        # Get target unit
        target_unit = game.get_unit_at(target_pos[0], target_pos[1])
        if not target_unit:
            return False
            
        # Check if target is an enemy (not same player)
        if target_unit.player == user.player:
            return False
            
        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x
            
        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target
                
        # Check if target is within range from the correct position
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False
            
        # Check line of sight
        from boneglaive.utils.coordinates import get_line, Position
        path = get_line(Position(from_y, from_x), Position(target_pos[0], target_pos[1]))
            
        # Check for obstacles along the path (excluding the start and end points)
        for pos in path[1:-1]:
            # Check if the position is blocked by terrain
            if not game.map.is_passable(pos.y, pos.x):
                return False
                
            # Check if position is blocked by another unit
            blocking_unit = game.get_unit_at(pos.y, pos.x)
            if blocking_unit:
                return False
            
        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])  
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} charges the estrangement beam targeting {target.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Estrange skill to phase a target out of normal spacetime."""
        from boneglaive.utils.message_log import message_log, MessageType
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        import curses
        
        # Get target unit
        target = game.get_unit_at(target_pos[0], target_pos[1])
        if not target:
            return False
            
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} fires an estrangement beam at {target.get_display_name()}!",
            MessageType.ABILITY,
            player=user.player,
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name()
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the path from user to target
            from boneglaive.utils.coordinates import get_line, Position
            path = get_line(Position(user.y, user.x), Position(target.y, target.x))
            
            # Get estrange animation sequence
            estrange_animation = ui.asset_manager.get_skill_animation_sequence('estrange')
            if not estrange_animation:
                estrange_animation = ['≡', '≢', '⋍', '≈', '~', '≈', '⋍', '≢', '≡']  # Fallback
            
            # Show a building effect at user position first
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                estrange_animation[:3],  # Use first few frames
                6,  # yellowish color
                0.1  # duration
            )
            
            # Animate the beam along the path
            for i, pos in enumerate(path[1:-1]):  # Skip first (user) and last (target) positions
                # Use middle portion of animation for beam travel
                beam_frame = estrange_animation[3 % len(estrange_animation)]
                ui.renderer.draw_tile(pos.y, pos.x, beam_frame, 6)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.05)
            
            # Show impact at target position
            ui.renderer.animate_attack_sequence(
                target.y, target.x,
                estrange_animation[-3:],  # Use last few frames
                6,  # yellowish color
                0.15  # duration
            )
            
            # Flash the target to show impact
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(target.type)] * 4
                color_ids = [6, 3 if target.player == 1 else 4] * 2  # Alternate yellow with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(target.y, target.x, tile_ids, color_ids, durations)
        
        # Apply damage
        damage = self.damage
        previous_hp = target.hp
        target.hp = max(0, target.hp - damage)
        
        # Add message that estrangement bypasses defenses
        message_log.add_message(
            f"The estrangement beam bypasses {target.get_display_name()}'s defenses!",
            MessageType.ABILITY,
            player=user.player,
            target_name=target.get_display_name()
        )
        
        # Log the damage
        message_log.add_combat_message(
            attacker_name=user.get_display_name(),
            target_name=target.get_display_name(),
            damage=damage,
            ability="Estrange",
            attacker_player=user.player,
            target_player=target.player
        )
        
        # Show damage number if UI is available
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{damage}"
            
            for i in range(3):
                ui.renderer.draw_text(target.y-1, target.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_text(target.y-1, target.x*2, damage_text, 7, attrs)
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
        
        # Apply estranged effect if not immune
        if not target.is_immune_to_effects():
            # Apply the estranged effect permanently (no duration)
            target.estranged = True
            
            # Log the effect application - using WARNING type for yellow text
            message_log.add_message(
                f"{target.get_display_name()} is phased out of normal spacetime!",
                MessageType.WARNING,
                player=user.player,
                target_name=target.get_display_name()
            )
            
            # Show phasing animation if UI is available
            if ui and hasattr(ui, 'renderer'):
                # Create "phasing" visual effect with tilting characters
                phase_animation = ['|', '/', '—', '\\', '|']
                
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    phase_animation,
                    19,  # Gray color (19 is the estrangement color)
                    0.1  # duration
                )
                
                # Make the target appear "faded" by changing its color temporarily
                if hasattr(ui, 'asset_manager'):
                    # Get the unit tile
                    unit_tile = ui.asset_manager.get_unit_tile(target.type)
                    
                    # Redraw the unit with the status effect - consistent with other status effects
                    ui.renderer.draw_tile(
                        target.y, target.x,
                        f"{unit_tile}~",  # Combine unit symbol with tilde (consistent with UI rendering)
                        19,  # Gray color for estranged units
                        curses.A_DIM  # Dim attribute for negative status effect
                    )
                    ui.renderer.refresh()
                    sleep_with_animation_speed(0.3)
        else:
            message_log.add_message(
                f"{target.get_display_name()} is immune to Estrange due to Stasiality!",
                MessageType.ABILITY,
                player=target.player,  # Use target's player for correct color coding
                target_name=target.get_display_name()
            )
            
            # Show immunity animation if UI is available
            if ui and hasattr(ui, 'renderer'):
                # Immunity effect - show a shield ripple
                shield_animation = ['(', '[', '{', '}', ']', ')']
                
                ui.renderer.animate_attack_sequence(
                    target.y, target.x,
                    shield_animation,
                    7,  # white color
                    0.1  # duration
                )
        
        # Check if target was defeated
        if target.hp <= 0:
            message_log.add_message(
                f"{target.get_display_name()} perishes!",
                MessageType.COMBAT,
                player=user.player,
                target=target.player,
                target_name=target.get_display_name()
            )
        
        # Redraw board after animations
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
        return True


class GraeExchangeSkill(ActiveSkill):
    """Active skill for GRAYMAN. Creates an echo that can attack but not move."""
    
    def __init__(self):
        super().__init__(
            name="Græ Exchange",
            key="G",
            description="Create an echo at current position and teleport away. Echo can attack but not move.",
            target_type=TargetType.AREA,
            cooldown=4,
            range_=3
        )
    
    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        # Basic validation
        if not super().can_use(user, target_pos, game):
            return False
        if not game or not target_pos:
            return False

        # Target position must be valid and passable
        if not game.is_valid_position(target_pos[0], target_pos[1]):
            return False

        # Target position must be passable terrain
        if not game.map.is_passable(target_pos[0], target_pos[1]):
            return False

        # Target position must be empty (no unit)
        if game.get_unit_at(target_pos[0], target_pos[1]) is not None:
            return False

        # Check if any other unit is already planning to teleport to this position
        # (via Vault, Delta Config, Grae Exchange, or any other teleport skill)
        for other_unit in game.units:
            if (other_unit.is_alive() and other_unit != user):
                # Check for vault targets
                if (hasattr(other_unit, 'vault_target_indicator') and
                    other_unit.vault_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

                # Check for teleport targets (Delta Config, Grae Exchange, etc.)
                if (hasattr(other_unit, 'teleport_target_indicator') and
                    other_unit.teleport_target_indicator == target_pos):
                    from boneglaive.utils.message_log import message_log, MessageType
                    message_log.add_message(
                        f"Cannot teleport to this position.",
                        MessageType.WARNING,
                        player=user.player
                    )
                    return False

        # Use the correct starting position (current position or planned move position)
        from_y = user.y
        from_x = user.x

        # If unit has a planned move, use that position instead
        if user.move_target:
            from_y, from_x = user.move_target

        # Check if target is within range from the correct position
        distance = game.chess_distance(from_y, from_x, target_pos[0], target_pos[1])
        if distance > self.range:
            return False

        return True
            
    def use(self, user: 'Unit', target_pos: Optional[tuple] = None, game: Optional['Game'] = None) -> bool:
        if not self.can_use(user, target_pos, game):
            return False
        user.skill_target = target_pos
        user.selected_skill = self
        
        # Set teleport target indicator for UI
        user.teleport_target_indicator = target_pos
        
        # Log that the skill has been readied
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} initiates the Græ Exchange ritual targeting position ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        self.current_cooldown = self.cooldown
        return True
        
    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute the Græ Exchange skill - create an echo at current position and teleport away."""
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.utils.debug import logger
        import time
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed

        
        # Clear the teleport target indicator after execution
        user.teleport_target_indicator = None
        
        # Store original position for creating the echo
        original_pos = (user.y, user.x)
        
        # Log the skill activation
        message_log.add_message(
            f"{user.get_display_name()} begins the Græ Exchange ritual!",
            MessageType.ABILITY,
            player=user.player
        )
        
        # Play animation if UI is available
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get the animation sequence
            exchange_animation = ui.asset_manager.get_skill_animation_sequence('grae_exchange')
            if not exchange_animation:
                exchange_animation = ['/', '_', '*', 'ψ', 'Ψ']  # Fallback
            
            # Play initial animation at user's position
            ui.renderer.animate_attack_sequence(
                user.y, user.x,
                exchange_animation,
                6,  # yellowish color
                0.15  # duration
            )
            
            # Flash the current position to emphasize the echo creation
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 6
                color_ids = [6, 3 if user.player == 1 else 4] * 3  # Alternate yellow with player color
                durations = [0.1] * 6
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        
        # Create an echo unit at the original position - BEFORE moving the user
        from boneglaive.game.units import Unit
        echo_unit = Unit(user.type, user.player, original_pos[0], original_pos[1])
        echo_unit.initialize_skills()
        echo_unit.set_game_reference(game)
        
        # Set echo properties
        echo_unit.is_echo = True
        echo_unit.echo_duration = 2  # Echo lasts 2 turns
        echo_unit.original_unit = user
        echo_unit.hp = 5  # Echo has 5 HP and cannot be healed
        
        # Set attack value for echo unit to exactly 3 (regardless of original unit's attack)
        echo_unit.attack = 3  # Increased from 2 to 3
        
        # Add Greek letter identifier like other units - to make it more obvious in the UI
        if hasattr(user, 'greek_id') and user.greek_id:
            # Use the same letter but lowercase to indicate it's an echo
            echo_unit.greek_id = user.greek_id.lower()
        
        # Log explicit debug message about echo creation
        logger.info(f"ECHO UNIT CREATED: {echo_unit.type.name} at position ({original_pos[0]}, {original_pos[1]}) with {echo_unit.hp} HP")
        
        # Now teleport the user to the target position
        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
            # Get teleport out animation sequence
            teleport_out = ui.asset_manager.get_skill_animation_sequence('teleport_out')
            if not teleport_out:
                teleport_out = ['Ψ', '░', '▒', '▓', ' ']  # Fallback
            
            # Get teleport in animation sequence
            teleport_in = ui.asset_manager.get_skill_animation_sequence('teleport_in')
            if not teleport_in:
                teleport_in = [' ', '▓', '▒', '░', 'Ψ']  # Fallback
            
            # Temporarily hide the real unit
            temp_y, temp_x = user.y, user.x
            user.y, user.x = -999, -999  # Move off-screen
            
            # Add the echo unit to the game AFTER hiding the original unit
            game.units.append(echo_unit)
            
            # Redraw to show the echo in the original position and the real unit gone
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                ui.renderer.refresh()
            
            # Pause for effect
            sleep_with_animation_speed(0.3)
            
            # Show the teleport to the new position
            ui.renderer.animate_attack_sequence(
                target_pos[0], target_pos[1],
                teleport_in,
                7,  # white color
                0.15  # duration
            )
            
            # Actually move the unit to the target position
            user.y, user.x = target_pos
            
            # Redraw to show the final state
            if hasattr(ui, 'draw_board'):
                ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
                ui.renderer.refresh()
                
            # Flash the moved unit to emphasize completion
            if hasattr(ui, 'asset_manager'):
                tile_ids = [ui.asset_manager.get_unit_tile(user.type)] * 4
                color_ids = [7, 3 if user.player == 1 else 4] * 2  # Alternate white with player color
                durations = [0.1] * 4
                
                ui.renderer.flash_tile(user.y, user.x, tile_ids, color_ids, durations)
        else:
            # No UI, just set position without animations
            # Add the echo unit to the game 
            game.units.append(echo_unit)
            # Move the user to the target position
            user.y, user.x = target_pos
        
        # Log the completion
        message_log.add_message(
            f"{user.get_display_name()} creates an echo and teleports to ({target_pos[0]}, {target_pos[1]})!",
            MessageType.ABILITY,
            player=user.player
        )
        
        return True