#!/usr/bin/env python3
"""
Unit classes and related functionality for Boneglaive.
"""
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from boneglaive.utils.constants import UNIT_STATS, UnitType, MAX_LEVEL, XP_PER_LEVEL

if TYPE_CHECKING:
    from boneglaive.game.skills.core import Skill, PassiveSkill, ActiveSkill
    from boneglaive.game.engine import Game

class Unit:
    """Base class for all units in the game."""
    
    def __init__(self, unit_type, player, y, x):
        # Basic unit properties
        self.type = unit_type
        self.player = player  # 1 or 2
        
        # Use private attributes for position to enable property setters
        self._y = y
        self._x = x
        
        # Game reference for trap checks (will be set by engine)
        self._game = None
        
        # Greek letter identifier (assigned later when all units are spawned)
        self.greek_id = None
        
        # Get base stats from constants
        base_hp, base_attack, base_defense, base_move_range, base_attack_range = UNIT_STATS[unit_type]
        
        # Current and maximum stats
        self.max_hp = base_hp
        self.hp = self.max_hp
        self.attack = base_attack
        self.defense = base_defense
        self.move_range = base_move_range
        self.attack_range = base_attack_range
        
        # Stat bonuses from skills/items/etc.
        self.hp_bonus = 0
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.move_range_bonus = 0
        self.attack_range_bonus = 0
        
        # Action targets
        self.move_target = None
        self.attack_target = None
        self.skill_target = None
        self.selected_skill = None
        
        # Visual indicators for skills
        self.vault_target_indicator = None  # Visual indicator for Vault destination
        self.site_inspection_indicator = None  # Visual indicator for Site Inspection area
        self.teleport_target_indicator = None  # Visual indicator for Delta Config destination
        self.expedite_path_indicator = None  # Visual indicator for Expedite path
        self.jawline_indicator = None  # Visual indicator for Jawline network area
        
        # Action order tracking (lower is earlier)
        self.action_timestamp = 0
        
        # Status effects
        self.was_pried = False  # Track if this unit was affected by Pry skill
        self.trapped_by = None  # Reference to MANDIBLE_FOREMAN that trapped this unit, None if not trapped
        self.trap_duration = 0  # Number of turns this unit has been trapped, for incremental damage
        self.took_action = False  # Track if this unit took an action this turn
        self.jawline_affected = False  # Track if unit is affected by Jawline skill
        self.jawline_duration = 0  # Duration remaining for Jawline effect
        self.estranged = False  # Track if unit is affected by Estrange skill
        
        # Græ Exchange echo properties
        self.is_echo = False  # Whether this unit is an echo created by Græ Exchange
        self.echo_duration = 0  # Number of OWNER'S turns the echo remains (decremented only on owner's turn)
        self.original_unit = None  # Reference to the original unit that created this echo
        
        # HEINOUS VAPOR properties (for GAS_MACHINIST)
        self.vapor_type = None  # Type of vapor ("ENBROACHMENT", "SAFETY", "COOLANT", or "CUTTING")
        self.vapor_symbol = None  # Symbol to display for this vapor (Φ, Θ, Σ, %)
        self.vapor_duration = 0  # Number of turns the vapor remains
        self.vapor_creator = None  # Reference to the GAS_MACHINIST that created this vapor
        self.vapor_skill = None  # Reference to the skill that created this vapor
        self.diverged_user = None  # Reference to the GAS_MACHINIST if this vapor is from a diverged user
        
        # GAS_MACHINIST properties
        self.diverge_return_position = False  # Whether this unit is returning from a diverge
        
        # Experience and leveling
        self.level = 1
        self.xp = 0
        
        # Skills (will be initialized after import to avoid circular imports)
        self.passive_skill = None
        self.active_skills = []
        
    def initialize_skills(self) -> None:
        """Initialize skills for this unit based on its type."""
        # Avoid circular imports
        from boneglaive.game.skills.registry import UNIT_SKILLS
        
        # Get skills from registry if available
        unit_type_name = self.type.name
        if unit_type_name in UNIT_SKILLS:
            skill_set = UNIT_SKILLS[unit_type_name]
            
            # Set passive skill - create new instance for each unit
            if 'passive' in skill_set:
                passive_class = skill_set['passive'].__class__
                self.passive_skill = passive_class()
                
            # Set active skills - create new instances for each unit
            if 'active' in skill_set:
                self.active_skills = []
                for skill in skill_set['active']:
                    # Create a new instance of the skill for this unit
                    skill_class = skill.__class__
                    self.active_skills.append(skill_class())
    
    def is_alive(self) -> bool:
        """Check if the unit is alive."""
        return self.hp > 0
        
    def is_at_critical_health(self) -> bool:
        """Check if the unit is at critical health threshold."""
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        critical_threshold = int(self.max_hp * CRITICAL_HEALTH_PERCENT)
        return self.hp > 0 and self.hp <= critical_threshold
        
    def get_critical_threshold(self) -> int:
        """Get the HP threshold for critical health."""
        from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
        return int(self.max_hp * CRITICAL_HEALTH_PERCENT)
    
    def get_effective_stats(self) -> Dict[str, int]:
        """Get the unit's effective stats including bonuses and penalties."""
        # If unit has Stasiality, return base stats only (immune to all changes)
        if self.is_immune_to_effects():
            return {
                'hp': self.max_hp,  # HP bonuses are still tracked separately
                'attack': self.attack,
                'defense': self.defense,
                'move_range': self.move_range, 
                'attack_range': self.attack_range
            }
            
        # For all other units, apply bonuses and penalties normally
        # Apply Estrange effect (-1 to all stats) if unit is estranged
        estrange_penalty = -1 if self.estranged else 0
        
        # Calculate base stats with bonuses
        stats = {
            'hp': self.max_hp + self.hp_bonus,
            'attack': max(1, self.attack + self.attack_bonus + estrange_penalty),
            'defense': max(0, self.defense + self.defense_bonus + estrange_penalty),
            'attack_range': max(1, self.attack_range + self.attack_range_bonus + estrange_penalty)
        }
        
        # Special handling for move_range - allow it to be 0 for Jawline effect
        # This ensures full immobilization when affected by Jawline
        if hasattr(self, 'jawline_affected') and self.jawline_affected:
            # When Jawline is active, movement can be reduced to 0
            stats['move_range'] = max(0, self.move_range + self.move_range_bonus + estrange_penalty)
        else:
            # Normal minimum of 1 for all other cases
            stats['move_range'] = max(1, self.move_range + self.move_range_bonus + estrange_penalty)
        
        
        # If unit is an echo (from Græ Exchange), set its attack to at least 2
        if self.is_echo:
            # For GRAYMAN echoes, use half attack but with a minimum of 2
            halved_attack = stats['attack'] // 2
            stats['attack'] = max(2, halved_attack)
            # Echo cannot move
            stats['move_range'] = 0
            
        return stats
        
    def get_display_name(self, shortened=False) -> str:
        """Get the unit's display name including the Greek identifier.
        
        Args:
            shortened: If True, provides a shorter display name for UI menus
        """
        # Format unit type name for display (replace underscores with spaces)
        display_type = self.type.name
        if display_type == "MANDIBLE_FOREMAN":
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "M.FOREMAN"
            else:
                display_type = "MANDIBLE FOREMAN"
        elif display_type == "MARROW_CONDENSER":
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "M.CONDENSER"
            else:
                display_type = "MARROW CONDENSER"
        elif display_type == "HEINOUS_VAPOR":
            # Special handling for HEINOUS_VAPOR units
            if hasattr(self, 'vapor_type') and self.vapor_type:
                if self.vapor_type == "BROACHING":
                    vapor_name = "BROACHING GAS"
                elif self.vapor_type == "SAFETY":
                    vapor_name = "SAFT-E-GAS"
                elif self.vapor_type == "COOLANT":
                    vapor_name = "COOLANT GAS"
                elif self.vapor_type == "CUTTING":
                    vapor_name = "CUTTING GAS"
                else:
                    vapor_name = "HEINOUS VAPOR"
                
                # Include the symbol in the name
                if hasattr(self, 'vapor_symbol') and self.vapor_symbol:
                    if shortened:
                        return f"{self.vapor_symbol}"
                    else:
                        return f"{vapor_name} {self.vapor_symbol}"
                else:
                    return vapor_name
            else:
                return "HEINOUS VAPOR"
        elif display_type == "FOWL_CONTRIVANCE":
            display_type = "FOWL CONTRIVANCE"
        elif display_type == "GAS_MACHINIST":
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "G.MACHINIST"
            else:
                display_type = "GAS MACHINIST"
        
        # For echo units, change name to "ECHO {TYPE}"
        if self.is_echo:
            if self.greek_id:
                return f"ECHO {display_type} {self.greek_id}"
            else:
                return f"ECHO {display_type}"
        else:
            if self.greek_id:
                return f"{display_type} {self.greek_id}"
            else:
                return f"{display_type}"
    
    def apply_passive_skills(self, game=None) -> None:
        """Apply effects of passive skills."""
        if self.passive_skill:
            self.passive_skill.apply_passive(self, game)
            
    def is_immune_to_effects(self) -> bool:
        """Check if this unit has immunity to status effects and debuffs.
        Currently only GRAYMAN with Stasiality passive has this immunity.
        Note: This does NOT grant immunity to physical traps like Viseroy."""
        return self.passive_skill and self.passive_skill.name == "Stasiality"
        
    def is_immune_to_trap(self) -> bool:
        """Check if this unit is immune to being trapped.
        By default, no units are immune to physical traps."""
        return False
    
    def get_available_skills(self) -> List:
        """
        Get list of available active skills (not on cooldown).
        """
        # Just check cooldown for all skills
        return [skill for skill in self.active_skills if skill.current_cooldown == 0]
    
    def tick_cooldowns(self) -> None:
        """
        Reduce cooldowns for all skills by 1 turn.
        This is called at the end of a player's turn, only for that player's units.
        A skill with cooldown=1 can be used every turn, cooldown=2 every other turn, etc.
        Movement penalties are handled separately in reset_movement_penalty.
        """
        # Tick skill cooldowns
        for skill in self.active_skills:
            skill.tick_cooldown()
        
        # Movement penalties are now handled in reset_movement_penalty method
        # which is called at the beginning of a player's turn
    
    def add_xp(self, amount: int) -> bool:
        """
        Add XP to the unit and level up if threshold reached.
        Returns True if unit leveled up.
        
        Note: Currently disabled - no XP gain will occur.
        """
        # XP gain is temporarily disabled
        return False
    
    def level_up(self) -> None:
        """Increase unit level and improve stats."""
        if self.level >= MAX_LEVEL:
            return
            
        self.level += 1
        
        # Improve stats based on unit type (can be customized per unit type)
        if self.type == UnitType.GLAIVEMAN:
            self.max_hp += 5
            self.attack += 2
            self.defense += 2
        elif self.type == UnitType.ARCHER:
            self.max_hp += 3
            self.attack += 3
            self.defense += 1
        elif self.type == UnitType.MAGE:
            self.max_hp += 2
            self.attack += 4
            self.defense += 1
        elif self.type == UnitType.MANDIBLE_FOREMAN:
            self.max_hp += 6  # Focus on increasing durability
            self.attack += 2
            self.defense += 3
        
        # Heal unit when leveling up
        self.hp = self.max_hp
        
    def reset_action_targets(self) -> None:
        """Reset all action targets."""
        # Check if the unit took any action this turn that should release trapped units
        # For MANDIBLE_FOREMAN, using Recalibrate shouldn't count as an action that releases trapped units
        
        # By default, any movement, attack, or skill use counts as an action
        took_action = (self.move_target is not None or 
                      self.attack_target is not None or 
                      self.skill_target is not None)
                      
        # No special cases anymore
            
        # Set the took_action flag
        self.took_action = took_action
        
        # Clear all action targets
        self.move_target = None
        self.attack_target = None
        self.skill_target = None
        self.selected_skill = None
        
        # Clear visual indicators
        self.vault_target_indicator = None
        self.site_inspection_indicator = None
        self.teleport_target_indicator = None
        self.expedite_path_indicator = None
        self.jawline_indicator = None
        
        self.action_timestamp = 0  # Reset the action timestamp
        # No Recalibrate tracking
        
    # Position properties with trap release functionality
    @property
    def y(self):
        return self._y
        
    @y.setter
    def y(self, value):
        # Store old position for trap checks
        old_y = self._y
        
        # Update position
        self._y = value
        
        # Only check if position actually changed and game reference exists
        if old_y != value and self._game:
            # Case 1: If this is a MANDIBLE_FOREMAN, check for trap release
            if self.type == UnitType.MANDIBLE_FOREMAN:
                self._game._check_position_change_trap_release(self, old_y, self._x)
                
            # Case 2: If this unit is trapped, check for trap release
            if self.trapped_by is not None:
                self._game._check_position_change_trap_release(self, old_y, self._x)
            
    @property
    def x(self):
        return self._x
        
    @x.setter
    def x(self, value):
        # Store old position for trap checks
        old_x = self._x
        
        # Update position
        self._x = value
        
        # Only check if position actually changed and game reference exists
        if old_x != value and self._game:
            # Case 1: If this is a MANDIBLE_FOREMAN, check for trap release
            if self.type == UnitType.MANDIBLE_FOREMAN:
                self._game._check_position_change_trap_release(self, self._y, old_x)
                
            # Case 2: If this unit is trapped, check for trap release
            if self.trapped_by is not None:
                self._game._check_position_change_trap_release(self, self._y, old_x)
    
    def set_game_reference(self, game):
        """Set reference to the game for trap checks."""
        self._game = game
            
    def reset_movement_penalty(self) -> None:
        """Clear any movement penalties and reset relevant status flags."""
        # Do not reset move_range_bonus if affected by Jawline
        if not self.jawline_affected and self.move_range_bonus < 0:
            self.move_range_bonus = 0
            
        # NOTE: Jawline duration is now decremented in Game.execute_turn
        # to ensure it only happens on the player's own turn
        
        # Reset the Pry status effect - with debug logging
        if hasattr(self, 'pry_duration') and self.pry_duration > 0:
            # Log the current state
            from boneglaive.utils.debug import logger
            logger.info(f"Pry status for {self.get_display_name()}: duration={self.pry_duration}, active={getattr(self, 'pry_active', False)}, was_pried={self.was_pried}")
            
            # Decrement the duration
            self.pry_duration -= 1
            
            # If duration expired, clear the effect
            if self.pry_duration <= 0:
                logger.info(f"Clearing Pry effect for {self.get_display_name()}")
                self.was_pried = False
                self.pry_active = False
                if hasattr(self, 'pry_duration'):
                    delattr(self, 'pry_duration')
            
        # For backward compatibility - reset was_pried if no duration
        elif self.was_pried:
            self.was_pried = False
            if hasattr(self, 'pry_active'):
                self.pry_active = False
                
    def apply_vapor_effects(self, game: 'Game', ui=None) -> None:
        """
        Apply area effects for HEINOUS_VAPOR units.
        This is called during combat phase processing.
        Note: The game engine only calls this method for vapors belonging to the current player.
        """
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        import curses
        from boneglaive.utils.animation_helpers import sleep_with_animation_speed
        
        # Only process if this is a HEINOUS_VAPOR
        if self.type != UnitType.HEINOUS_VAPOR or not hasattr(self, 'vapor_type') or not self.vapor_type:
            return
            
        # Define the 3x3 area around the vapor
        affected_area = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                ny, nx = self.y + dy, self.x + dx
                if game.is_valid_position(ny, nx):
                    affected_area.append((ny, nx))
                    
        # Play visual effect if UI is available
        if ui and hasattr(ui, 'renderer'):
            # Get appropriate animation based on vapor type
            animation_name = f"vapor_{self.vapor_type.lower()}"
            vapor_animation = ui.asset_manager.get_skill_animation_sequence(animation_name)
            if not vapor_animation:
                # Fallback animations based on vapor type
                if self.vapor_type == "BROACHING":
                    vapor_animation = ['~', '*', '+']
                elif self.vapor_type == "SAFETY":
                    vapor_animation = ['~', 'o', 'O']
                elif self.vapor_type == "COOLANT":
                    vapor_animation = ['~', '*', '+']
                elif self.vapor_type == "CUTTING":
                    vapor_animation = ['~', '%', '#']
                else:
                    vapor_animation = ['~', 'o', 'O']
            
            # Show visual effect in the area
            for pos in affected_area:
                y, x = pos
                
                # Use a subset of the animation for surrounding tiles
                if y == self.y and x == self.x:
                    # Center tile gets full animation
                    anim_sequence = vapor_animation
                    color = 7  # White for center
                else:
                    # Surrounding tiles get shorter animation
                    anim_sequence = vapor_animation[:2]
                    
                    # Choose color based on vapor type
                    if self.vapor_type == "BROACHING":
                        color = 5  # Purple
                    elif self.vapor_type == "SAFETY":
                        color = 3  # Yellow
                    elif self.vapor_type == "COOLANT":
                        color = 6  # Cyan/blue
                    elif self.vapor_type == "CUTTING":
                        color = 1  # Red
                    else:
                        color = 7  # White default
                
                # Animate this position
                ui.renderer.animate_attack_sequence(
                    y, x,
                    anim_sequence,
                    color,
                    0.05  # Quick animation
                )
        
        # Find units in the affected area
        affected_units = []
        for pos in affected_area:
            y, x = pos
            unit = game.get_unit_at(y, x)
            if unit and unit.is_alive():
                affected_units.append(unit)
                
        # Process effects based on vapor type
        if self.vapor_type == "BROACHING":
            # Broaching Gas: Damages enemies (2 damage) and cleanses allies of status effects
            for unit in affected_units:
                if unit.player != self.player:
                    # Enemy unit - apply damage
                    damage = 2
                    previous_hp = unit.hp
                    unit.hp = max(0, unit.hp - damage)
                    
                    # Log damage
                    message_log.add_combat_message(
                        attacker_name=self.get_display_name(),
                        target_name=unit.get_display_name(),
                        damage=damage,
                        ability="Broaching Gas",
                        attacker_player=self.player,
                        target_player=unit.player
                    )
                    
                    # Show damage number if UI is available
                    if ui and hasattr(ui, 'renderer'):
                        damage_text = f"-{damage}"
                        
                        ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 5, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                        
                    # Check if unit was defeated
                    if unit.hp <= 0:
                        message_log.add_message(
                            f"{unit.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=self.player,
                            target=unit.player,
                            target_name=unit.get_display_name()
                        )
                        
                elif unit.player == self.player and unit != self:
                    # Ally unit - cleanse status effects
                    effects_cleansed = []
                    
                    # Check for status effects to cleanse
                    if unit.estranged:
                        unit.estranged = False
                        effects_cleansed.append("Estrangement")
                        
                    if unit.was_pried or (hasattr(unit, 'pry_active') and unit.pry_active):
                        unit.was_pried = False
                        if hasattr(unit, 'pry_active'):
                            unit.pry_active = False
                        if unit.move_range_bonus < 0:
                            unit.move_range_bonus = 0
                        effects_cleansed.append("Pry movement penalty")
                        
                    if unit.jawline_affected:
                        unit.jawline_affected = False
                        unit.jawline_duration = 0
                        if unit.move_range_bonus < 0:
                            unit.move_range_bonus = 0
                        effects_cleansed.append("Jawline immobilization")
                        
                    # Log cleansed effects
                    if effects_cleansed:
                        message_log.add_message(
                            f"{unit.get_display_name()} is cleansed of {', '.join(effects_cleansed)}!",
                            MessageType.ABILITY,
                            player=self.player
                        )
                        
                        # Show cleansing effect if UI is available
                        if ui and hasattr(ui, 'renderer') and hasattr(ui, 'asset_manager'):
                            cleanse_animation = ui.asset_manager.get_skill_animation_sequence('cleanse')
                            if not cleanse_animation:
                                cleanse_animation = ['*', '+', 'o', '.']
                                
                            ui.renderer.animate_attack_sequence(
                                unit.y, unit.x,
                                cleanse_animation,
                                6,  # Cyan/blue
                                0.1
                            )
                            
                            # Flash the unit to show cleansing
                            if hasattr(ui, 'asset_manager'):
                                tile_ids = [ui.asset_manager.get_unit_tile(unit.type)] * 4
                                color_ids = [6, 3 if unit.player == 1 else 4] * 2  # Alternate cyan with player color
                                durations = [0.1] * 4
                                
                                ui.renderer.flash_tile(unit.y, unit.x, tile_ids, color_ids, durations)
                    
        elif self.vapor_type == "SAFETY":
            # Saft-E-Gas: Blocks enemy ranged attacks (handled elsewhere) and heals allies by 1
            for unit in affected_units:
                if unit.player == self.player and unit != self and unit.hp < unit.max_hp:
                    # Heal ally unit
                    healing = 1
                    unit.hp = min(unit.max_hp, unit.hp + healing)
                    
                    # Log healing
                    message_log.add_message(
                        f"{self.get_display_name()} heals {unit.get_display_name()} for {healing} HP!",
                        MessageType.ABILITY,
                        player=self.player
                    )
                    
                    # Show healing effect if UI is available
                    if ui and hasattr(ui, 'renderer'):
                        healing_text = f"+{healing}"
                        
                        ui.renderer.draw_text(unit.y-1, unit.x*2, healing_text, 3, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                        
                        # Flash the unit to show healing
                        if hasattr(ui, 'asset_manager'):
                            tile_ids = [ui.asset_manager.get_unit_tile(unit.type)] * 4
                            color_ids = [3, 3 if unit.player == 1 else 4] * 2  # Alternate green with player color
                            durations = [0.1] * 4
                            
                            ui.renderer.flash_tile(unit.y, unit.x, tile_ids, color_ids, durations)
                            
        elif self.vapor_type == "COOLANT":
            # Coolant Gas: Heals allies by 3 HP
            for unit in affected_units:
                if unit.player == self.player and unit != self and unit.hp < unit.max_hp:
                    # Heal ally unit
                    healing = 3
                    unit.hp = min(unit.max_hp, unit.hp + healing)
                    
                    # Log healing
                    message_log.add_message(
                        f"{self.get_display_name()} heals {unit.get_display_name()} for {healing} HP!",
                        MessageType.ABILITY,
                        player=self.player
                    )
                    
                    # Show healing effect if UI is available
                    if ui and hasattr(ui, 'renderer'):
                        healing_text = f"+{healing}"
                        
                        ui.renderer.draw_text(unit.y-1, unit.x*2, healing_text, 3, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                        
                        # Flash the unit to show healing
                        if hasattr(ui, 'asset_manager'):
                            tile_ids = [ui.asset_manager.get_unit_tile(unit.type)] * 4
                            color_ids = [3, 3 if unit.player == 1 else 4] * 2  # Alternate green with player color
                            durations = [0.1] * 4
                            
                            ui.renderer.flash_tile(unit.y, unit.x, tile_ids, color_ids, durations)
                            
        elif self.vapor_type == "CUTTING":
            # Cutting Gas: Deals 3 pierce damage to enemies (bypasses defense)
            for unit in affected_units:
                if unit.player != self.player:
                    # Enemy unit - apply piercing damage
                    damage = 3  # Pierce damage ignores defense
                    previous_hp = unit.hp
                    unit.hp = max(0, unit.hp - damage)
                    
                    # Log damage
                    message_log.add_message(
                        f"{self.get_display_name()} deals {damage} piercing damage to {unit.get_display_name()}!",
                        MessageType.ABILITY,
                        player=self.player
                    )
                    
                    message_log.add_combat_message(
                        attacker_name=self.get_display_name(),
                        target_name=unit.get_display_name(),
                        damage=damage,
                        ability="Cutting Gas",
                        attacker_player=self.player,
                        target_player=unit.player
                    )
                    
                    # Show damage number if UI is available
                    if ui and hasattr(ui, 'renderer'):
                        damage_text = f"-{damage}"
                        
                        ui.renderer.draw_text(unit.y-1, unit.x*2, damage_text, 1, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.1)
                        
                    # Check if unit was defeated
                    if unit.hp <= 0:
                        message_log.add_message(
                            f"{unit.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=self.player,
                            target=unit.player,
                            target_name=unit.get_display_name()
                        )
                        
        # Redraw board after effects
        if ui and hasattr(ui, 'draw_board'):
            ui.draw_board(show_cursor=False, show_selection=False, show_attack_targets=False)
        
    def get_skill_by_key(self, key: str) -> Optional:
        """Get an active skill by its key (for UI selection)."""
        key = key.upper()
        for skill in self.active_skills:
            if skill.key.upper() == key:
                return skill
        return None