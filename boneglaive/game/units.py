#!/usr/bin/env python3
"""
Unit classes and related functionality for Boneglaive.
"""
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from boneglaive.utils.constants import UNIT_STATS, UnitType, MAX_LEVEL, XP_PER_LEVEL
from boneglaive.utils.debug import logger

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
        self._hp = self.max_hp  # Use private property with getters/setters
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
        # Old indicator removed - new skills have their own indicators
        # Old emetic flange indicator removed
        self.broaching_gas_indicator = None  # Visual indicator for Broaching Gas target
        self.saft_e_gas_indicator = None  # Visual indicator for Saft-E-Gas target
        self.market_futures_indicator = None  # Visual indicator for Market Futures furniture target
        self.divine_depreciation_indicator = None  # Visual indicator for Divine Depreciation furniture target
        self.auction_curse_enemy_indicator = None  # Visual indicator for enemy target of Auction Curse
        self.auction_curse_ally_indicator = None  # Visual indicator for ally target of Auction Curse
        
        # Action order tracking (lower is earlier)
        self.action_timestamp = 0
        
        # Status effects
        self.was_pried = False  # Track if this unit was affected by Pry skill
        self.trapped_by = None  # Reference to MANDIBLE_FOREMAN that trapped this unit, None if not trapped
        self.trap_duration = 0  # Number of turns this unit has been trapped, for incremental damage
        self.took_action = False  # Track if this unit took an action this turn (used by MANDIBLE_FOREMAN)
        self.took_no_actions = True  # Track if unit took no actions for health regeneration
        self.jawline_affected = False  # Track if unit is affected by Jawline skill
        self.jawline_duration = 0  # Duration remaining for Jawline effect
        self.estranged = False  # Track if unit is affected by Estrange skill
        self.mired = False  # Track if unit is affected by upgraded Marrow Dike
        self.mired_duration = 0  # Duration remaining for mired effect
        
        # Græ Exchange echo properties
        self.is_echo = False  # Whether this unit is an echo created by Græ Exchange
        self.echo_duration = 0  # Number of OWNER'S turns the echo remains (decremented only on owner's turn)
        self.original_unit = None  # Reference to the original unit that created this echo
        
        # FOWL_CONTRIVANCE properties
        self.charging_status = False  # Whether this unit has "charging" status effect
        self.gaussian_charge_direction = None  # Direction for Gaussian Dusk charging
        self.gaussian_dusk_indicator = None  # Visual indicator for Gaussian Dusk charging
        self.big_arc_indicator = None  # Visual indicator for Big Arc area
        self.fragcrest_indicator = None  # Visual indicator for Fragcrest cone
        self.shrapnel_duration = 0  # Number of turns remaining for shrapnel damage
        
        # HEINOUS VAPOR properties (for GAS_MACHINIST)
        self.vapor_type = None  # Type of vapor ("ENBROACHMENT", "SAFETY", "COOLANT", or "CUTTING")
        self.vapor_symbol = None  # Symbol to display for this vapor (Φ, Θ, Σ, %)
        self.vapor_duration = 0  # Number of turns the vapor remains
        self.vapor_creator = None  # Reference to the GAS_MACHINIST that created this vapor
        self.vapor_skill = None  # Reference to the skill that created this vapor
        self.diverged_user = None  # Reference to the GAS_MACHINIST if this vapor is from a diverged user
        self.is_invulnerable = False  # Flag to make Heinous Vapor units invulnerable
        
        # GAS_MACHINIST properties
        self.diverge_return_position = False  # Whether this unit is returning from a diverge
        
        # INTERFERER properties
        self.radiation_stacks = []  # List of radiation durations (each stack lasts 2 turns)
        self.neural_shunt_affected = False  # Whether affected by Neural Shunt
        self.neural_shunt_duration = 0  # Duration of Neural Shunt effect
        self.carrier_rave_active = False  # Whether in Carrier Rave phased state
        self.carrier_rave_duration = 0  # Duration of Carrier Rave effect
        self.carrier_rave_strikes_ready = False  # Whether next attack will strike 3 times
        
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
        
        # Special handling for move_range - allow it to be 0 for Jawline effect and charging status
        # This ensures full immobilization when affected by these status effects
        if ((hasattr(self, 'jawline_affected') and self.jawline_affected) or 
            (hasattr(self, 'charging_status') and self.charging_status)):
            # When Jawline or charging is active, movement can be reduced to 0
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
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "F.CONTRIVANCE"
            else:
                display_type = "FOWL CONTRIVANCE"
        elif display_type == "GAS_MACHINIST":
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "G.MACHINIST"
            else:
                display_type = "GAS MACHINIST"
        elif display_type == "DELPHIC_APPRAISER":
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "D.APPRAISER"
            else:
                display_type = "DELPHIC APPRAISER"
        
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
        HEINOUS_VAPOR units are also immune to all status effects.
        Note: This includes immunity to physical traps like Viseroy."""
        # HEINOUS_VAPOR units are always immune to status effects
        if self.type == UnitType.HEINOUS_VAPOR:
            return True
        # GRAYMAN with Stasiality passive is immune
        return self.passive_skill and self.passive_skill.name == "Stasiality"

    def is_immune_to_trap(self) -> bool:
        """Check if this unit is immune to being trapped.
        GRAYMAN with Stasiality passive and HEINOUS_VAPOR units are immune to trapping effects."""
        # Use the general immunity check
        return self.is_immune_to_effects()
    
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
    
    def can_move_to(self, y: int, x: int, game=None) -> bool:
        """
        Check if this unit can move to the specified position.
        FOWL_CONTRIVANCE units can only move along rail tiles.
        """
        if not game:
            return True  # No game context, allow move
            
        # FOWL_CONTRIVANCE movement restrictions
        if self.type == UnitType.FOWL_CONTRIVANCE:
            # Cannot move while charging Gaussian Dusk
            if hasattr(self, 'gaussian_charging') and self.gaussian_charging:
                return False
                
            # Must move along rails (if rails exist)
            if game.map.has_rails():
                from boneglaive.game.map import TerrainType
                terrain = game.map.get_terrain_at(y, x)
                return terrain == TerrainType.RAIL
            else:
                # No rails exist yet, can move normally
                return game.map.is_passable(y, x)
        
        # All other units can move normally
        return game.map.is_passable(y, x)
    
    def apply_shrapnel_damage(self, game=None) -> int:
        """
        Apply shrapnel damage at the start of turn if unit has embedded shrapnel.
        Returns the damage dealt.
        """
        if self.shrapnel_duration <= 0:
            return 0
            
        damage = 1  # Shrapnel always deals 1 damage
        self.hp = max(0, self.hp - damage)
        self.shrapnel_duration -= 1
        
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{self.get_display_name()} takes {damage} damage from embedded shrapnel!",
            MessageType.ABILITY,
            player=self.player
        )
        
        return damage
    
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
        
    # HP property with invulnerability check
    @property
    def hp(self):
        return self._hp
        
    @hp.setter
    def hp(self, value):
        # For HEINOUS_VAPOR with invulnerability flag, prevent HP reduction
        if self.type == UnitType.HEINOUS_VAPOR and hasattr(self, 'is_invulnerable') and self.is_invulnerable:
            # Only allow HP to increase, not decrease
            if value > self._hp:
                self._hp = value
            # Otherwise, log and ignore damage without adding a message
            else:
                from boneglaive.utils.debug import logger
                
                # Calculate attempted damage
                attempted_damage = self._hp - value
                if attempted_damage > 0:
                    # Only log to debug, don't add a message to the log
                    logger.debug(f"Invulnerable {self.get_display_name()} ignored {attempted_damage} damage")
        else:
            # Normal HP setting for all other units
            self._hp = value
            
    def expire(self):
        """Force unit expiration, bypassing invulnerability.
        Used when HEINOUS_VAPOR duration runs out."""
        self._hp = 0
    
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
        # First check for first-turn move bonus for player 2
        if hasattr(self, 'first_turn_move_bonus') and self.first_turn_move_bonus:
            # This buff only lasts for one turn
            if self.player == 2:
                # Remove the move bonus
                self.move_range_bonus -= 1
                # Clear the flag
                self.first_turn_move_bonus = False
                # Log the change
                from boneglaive.utils.debug import logger
                logger.info(f"Removing first turn move bonus for {self.get_display_name()}")

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
                        
                        # Make damage text more prominent with flashing effect (like FOWL_CONTRIVANCE)
                        for i in range(3):
                            # First clear the area
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                            # Draw with alternating bold/normal for a flashing effect
                            attrs = curses.A_BOLD if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)  # White color
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)
                        
                        # Final damage display (stays on screen slightly longer)
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.3)  # Match the 0.3s delay used in FOWL_CONTRIVANCE
                        
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
            # Saft-E-Gas performs two functions:
            # 1. Protection zone: Always active, prevents targeting of allied units inside
            # 2. Healing: Heals allies by 1 HP per tick
            
            # Grab reference to game for debugging
            game = self._game
            
            # First, find all units that were previously protected by this vapor but are no longer in range
            # We need to clean up their protection lists
            for game_unit in game.units:
                if (game_unit.is_alive() and 
                    hasattr(game_unit, 'protected_by_safety_gas') and 
                    game_unit.protected_by_safety_gas and
                    self in game_unit.protected_by_safety_gas and
                    game_unit not in affected_units):
                    
                    # Unit is no longer affected by this vapor - remove protection
                    game_unit.protected_by_safety_gas.remove(self)
                    logger.debug(f"{game_unit.get_display_name()} is no longer protected by {self.get_display_name()} (moved out of range)")
                    
                    # If there are no more protecting vapors, clean up the attribute
                    if not game_unit.protected_by_safety_gas:
                        logger.debug(f"{game_unit.get_display_name()} is no longer protected by any safety gas")
                        delattr(game_unit, 'protected_by_safety_gas')
                    # Double check - ensure the protecting vapor is actually in the game
                    elif hasattr(game, 'units') and self not in game.units:
                        if self in game_unit.protected_by_safety_gas:
                            game_unit.protected_by_safety_gas.remove(self)
                            logger.debug(f"{game_unit.get_display_name()} is no longer protected by removed vapor")
                            # If there are no more protecting vapors after this, clean up the attribute
                            if not game_unit.protected_by_safety_gas:
                                delattr(game_unit, 'protected_by_safety_gas')
            
            # PROTECTION EFFECT: Mark all allied units in the cloud as "protected by safety gas"
            # This allows the targeting code to know which units are protected
            for unit in affected_units:
                if unit.player == self.player and unit != self:
                    # Set a property on the unit to mark it as protected
                    if not hasattr(unit, 'protected_by_safety_gas'):
                        unit.protected_by_safety_gas = []
                        logger.debug(f"{unit.get_display_name()} is now protected by first safety gas")
                    if self not in unit.protected_by_safety_gas:
                        unit.protected_by_safety_gas.append(self)
                        logger.debug(f"{unit.get_display_name()} is now protected by safety gas from {self.get_display_name()}")
            
            # HEALING EFFECT: Heal allied units in the cloud
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
                        
                        # Make healing text prominent with flashing effect (green color)
                        for i in range(3):
                            # First clear the area
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(healing_text), 7)
                            # Draw with alternating bold/normal for a flashing effect
                            attrs = curses.A_BOLD if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, healing_text, 3, attrs)  # Green color
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)
                        
                        # Final healing display (stays on screen slightly longer)
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, healing_text, 3, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.3)
                        
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
                        
                        # Make healing text prominent with flashing effect (green color)
                        for i in range(3):
                            # First clear the area
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(healing_text), 7)
                            # Draw with alternating bold/normal for a flashing effect
                            attrs = curses.A_BOLD if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, healing_text, 3, attrs)  # Green color
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)
                        
                        # Final healing display (stays on screen slightly longer)
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, healing_text, 3, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.3)
                        
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
                        
                        # Make damage text more prominent with flashing effect (like FOWL_CONTRIVANCE)
                        for i in range(3):
                            # First clear the area
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, " " * len(damage_text), 7)
                            # Draw with alternating bold/normal for a flashing effect
                            attrs = curses.A_BOLD if i % 2 == 0 else 0
                            ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, attrs)  # White color
                            ui.renderer.refresh()
                            sleep_with_animation_speed(0.1)
                        
                        # Final damage display (stays on screen slightly longer)
                        ui.renderer.draw_damage_text(unit.y-1, unit.x*2, damage_text, 7, curses.A_BOLD)
                        ui.renderer.refresh()
                        sleep_with_animation_speed(0.3)  # Match the 0.3s delay used in FOWL_CONTRIVANCE
                        
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
    
    def apply_radiation_damage(self, game: 'Game', ui=None) -> int:
        """
        Apply radiation damage from all active radiation stacks.
        Returns total damage dealt.
        """
        if not hasattr(self, 'radiation_stacks') or not self.radiation_stacks:
            return 0
            
        total_damage = len(self.radiation_stacks)  # 1 damage per stack
        if total_damage <= 0:
            return 0
            
        # Apply damage
        self.hp = max(0, self.hp - total_damage)
        
        # Log radiation damage
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{self.get_display_name()} takes {total_damage} radiation damage!",
            MessageType.ABILITY,
            player=self.player
        )
        
        # Show damage animation
        if ui and hasattr(ui, 'renderer'):
            damage_text = f"-{total_damage}"
            import curses
            from boneglaive.utils.animation_helpers import sleep_with_animation_speed
            
            for i in range(3):
                ui.renderer.draw_damage_text(self.y-1, self.x*2, " " * len(damage_text), 7)
                attrs = curses.A_BOLD if i % 2 == 0 else 0
                ui.renderer.draw_damage_text(self.y-1, self.x*2, damage_text, 6, attrs)  # Yellow color
                ui.renderer.refresh()
                sleep_with_animation_speed(0.1)
        
        # Decrement all radiation stack durations
        self.radiation_stacks = [duration - 1 for duration in self.radiation_stacks if duration > 1]
        
        return total_damage
    
    def is_untargetable(self) -> bool:
        """Check if this unit is untargetable due to status effects."""
        # Units under Carrier Rave are untargetable
        if hasattr(self, 'carrier_rave_active') and self.carrier_rave_active:
            return True
            
        return False
    
    def can_be_targeted_by(self, attacker) -> bool:
        """Check if this unit can be targeted by a specific attacker."""
        # First check if this unit is globally untargetable
        if self.is_untargetable():
            return False
        
        # Units under CARRIER_RAVE cannot be targeted by enemy units
        if (hasattr(self, 'carrier_rave_active') and self.carrier_rave_active and 
            attacker.player != self.player):
            return False
            
        return True
    
    def process_interferer_effects(self, game: 'Game') -> None:
        """Process INTERFERER-specific status effects at end of turn."""
        # Process Carrier Rave duration
        if hasattr(self, 'carrier_rave_duration') and self.carrier_rave_duration > 0:
            self.carrier_rave_duration -= 1
            if self.carrier_rave_duration <= 0:
                self.carrier_rave_active = False
                
                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"{self.get_display_name()} phases back into reality without striking!",
                    MessageType.ABILITY,
                    player=self.player
                )
        
        # Process Neural Shunt duration
        if hasattr(self, 'neural_shunt_duration') and self.neural_shunt_duration > 0:
            self.neural_shunt_duration -= 1
            if self.neural_shunt_duration <= 0:
                self.neural_shunt_affected = False
                
                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"{self.get_display_name()} regains control of their actions!",
                    MessageType.ABILITY,
                    player=self.player
                )
        
    def get_skill_by_key(self, key: str) -> Optional:
        """Get an active skill by its key (for UI selection)."""
        key = key.upper()
        for skill in self.active_skills:
            if skill.key.upper() == key:
                return skill
        return None
        
    def take_damage(self, damage: int, source_unit=None, ability_name=None) -> int:
        """
        Apply damage to the unit and return the actual damage dealt.
        
        Args:
            damage: Amount of damage to apply
            source_unit: Unit causing the damage (for logging)
            ability_name: Name of the ability causing the damage (for logging)
            
        Returns:
            The actual amount of damage dealt
        """
        # Check for invulnerability directly
        if self.type == UnitType.HEINOUS_VAPOR and hasattr(self, 'is_invulnerable') and self.is_invulnerable and damage > 0:
            from boneglaive.utils.debug import logger
            
            # Only log to debug, don't add a message to the game log
            attacker_name = source_unit.get_display_name() if source_unit else (ability_name or "Attack")
            logger.debug(f"Invulnerable {self.get_display_name()} ignored {damage} damage from {attacker_name}")
            
            return 0
        
        # Store previous HP for damage calculation
        previous_hp = self.hp
        
        # Apply damage (the hp property setter will handle invulnerability)
        self.hp = max(0, self.hp - damage)
        
        # Calculate actual damage dealt
        actual_damage = previous_hp - self.hp
        
        # Return actual damage dealt
        return actual_damage