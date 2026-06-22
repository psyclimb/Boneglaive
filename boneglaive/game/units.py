#!/usr/bin/env python3
"""
Unit classes and related functionality for Boneglaive.
"""
from typing import List, Dict, Optional, TYPE_CHECKING
from boneglaive.utils.constants import UNIT_STATS, UnitType, INVULNERABLE_PRT
from boneglaive.utils.debug import logger

if TYPE_CHECKING:
    from boneglaive.game.skills.core import Skill, ActiveSkill
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
        self._applying_damage = False  # Flag to prevent infinite recursion
        self._prt_absorbed_this_action = False  # Flag to prevent duplicate partition messages

        # Game reference for trap checks and spatial grid updates (will be set by engine)
        self._game = None
        
        # Letter identifier (assigned later when all units are spawned)
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
        self.prt_bonus = 0
        if unit_type == UnitType.HEINOUS_VAPOR:
            self.prt = INVULNERABLE_PRT
        else:
            self.prt = 0
        
        # Track recent PRT applications for message log correction
        self.last_prt_absorbed = 0  # Amount of damage absorbed by PRT in the most recent attack
        
        # Action targets
        self.move_target = None
        self.attack_target = None
        self.skill_target = None
        self.selected_skill = None
        self.attack_queued_from = None  # Position at attack queue time (for Severance range validation)
        
        # Visual indicators for skills
        self.vault_target_indicator = None  # Visual indicator for Vault destination
        self.site_inspection_indicator = None  # Visual indicator for Site Inspection area
        self.teleport_target_indicator = None  # Visual indicator for Delta Config destination
        self.expedite_path_indicator = None  # Visual indicator for Expedite path
        self.jawline_indicator = None  # Visual indicator for Jawline network area
        self.broaching_gas_indicator = None  # Visual indicator for Broaching Gas target
        self.saft_e_gas_indicator = None  # Visual indicator for Saft-E-Gas target
        self.market_futures_indicator = None  # Visual indicator for Market Futures furniture target
        self.divine_depreciation_indicator = None  # Visual indicator for Divine Depreciation furniture target
        self.auction_curse_enemy_indicator = None  # Visual indicator for enemy target of Auction Curse
        self.auction_curse_ally_indicator = None  # Visual indicator for ally target of Auction Curse
        
        # Action order tracking (lower is earlier)
        self.action_timestamp = 0

        # Upgrade tracking
        self.upgraded_skills = set()  # Set of skill names that have been upgraded

        # Status effects
        self.was_pried = False
        self.was_pried_upgraded = False
        self.trapped_by = None
        self.trap_duration = 0
        self.took_action = False
        self.took_no_actions = True
        self.jawline_affected = False
        self.jawline_duration = 0
        self.status_disarmed = False
        self.status_disarmed_duration = 0
        self.viseroy_disarm_cooldown = 0
        self.status_imbued = False
        self.status_imbued_duration = 0
        self.status_imbued_player = None
        self.status_imbued_cosmic_value = None
        self.estranged = False
        self.estranged_duration = 0
        self.mired = False
        self.mired_duration = 0
        self.shredded = False
        self.shredded_duration = 0
        self.shredded_original_defense = 0

        # Player 2 gets +1 move on first turn to offset going second
        self.first_turn_move_bonus = False
        self.first_turn_move_bonus_duration = 0

        # Græ Exchange echo properties
        self.is_doppelganger = False
        self.doppelganger_duration = 0  # Decremented only on owner's turn
        self.original_unit = None

        # FOWL_CONTRIVANCE properties
        self.gaussian_dusk_recharge = 0
        self.parabol_indicator = None
        self.fragcrest_indicator = None
        self.shrapnel_duration = 0

        # HEINOUS VAPOR properties (for GAS_MACHINIST)
        self.vapor_type = None
        self.vapor_symbol = None
        self.vapor_duration = 0
        self.vapor_creator = None
        self.vapor_skill = None
        self.diverged_user = None

        # GAS_MACHINIST properties
        self.diverge_return_position = False

        # INTERFERER properties
        self.radiation_stacks = []
        self.neural_shunt_affected = False
        self.neural_shunt_duration = 0
        self.carrier_rave_active = False
        self.carrier_rave_duration = 0
        self.carrier_rave_strikes_ready = False

        # DELPHIC APPRAISER properties
        self.can_use_anchor = False

        # Market Futures investment tracking
        self.market_futures_bonus_applied = False
        self.market_futures_duration = 0
        self.market_futures_maturity = 1
        self.has_investment_effect = False

        # DERELICTIONIST properties
        self.trauma_processing_active = False
        self.trauma_processing_caster = None
        self.trauma_debt = 0
        self.derelicted = False
        self.derelicted_duration = 0
        self.partition_shield_active = False
        self.partition_shield_caster = None
        self.partition_shield_strength = 0
        self.partition_shield_duration = 0

        # DERELICTIONIST skill-then-move mechanics
        self.has_moved_first = False
        self.used_skill_this_turn = False
        self.can_move_post_skill = False

        # Severance: +1 movement until movement is issued
        self.severance_active = False
        self.severance_duration = 0

        self.pumped_up_active = False
        self.pumped_up_duration = 0

        # POTPOURRIST-related status effects
        self.demilune_debuffed = False
        self.demilune_debuffed_by = None
        self.demilune_debuff_duration = 0
        self.taunted_by = None
        self.taunt_duration = 0
        self.taunt_responded_this_turn = False
        self.geas_affected = False
        self.geas_attack_reduction = False
        self.potpourri_held = False
        self.potpourri_duration = 0
        self.selenic_backdraft = False
        self.selenic_backdraft_by = None
        self.selenic_backdraft_duration = 0

        # LANDSCAPER Topiary Breath
        self.is_topiary = False
        self.topiary_duration = 0

        # ORDNANCE GRAFT — bombs (a target carries these; detonated by Harvest).
        # Each bomb is a distinct, individually-cleansable instance: {'fused': bool}.
        # A bomb arms (fuses) one turn after being planted and can only detonate once
        # fused. len(bombs) is the stack count (capped at BOMB_MAX_STACKS); drip-cleanse
        # (Broaching Gas) removes ONE bomb, a full cleanse (Vagal Run) removes all.
        self.bombs = []
        # ORDNANCE GRAFT — the leashed drone summon (set on the graft unit).
        self.is_drone = False          # True on an ORDNANCE_DRONE
        self.creator = None            # back-ref: drone -> its ORDNANCE_GRAFT owner
        self.drone = None              # forward-ref: graft -> its living drone (or None)
        self.drone_regen_timer = 0     # turns until a missing drone regenerates

        # Skills (will be initialized after import to avoid circular imports)
        self.passive_skill = None
        self.active_skills = []
        
    def initialize_skills(self) -> None:
        """Initialize skills for this unit based on its type."""
        # Avoid circular imports
        from boneglaive.game.skills.registry import UNIT_SKILLS

        # Get skills from registry if available
        if self.type in UNIT_SKILLS:
            skill_set = UNIT_SKILLS[self.type]

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

    def get_active_skills(self) -> List['ActiveSkill']:
        """
        Get all active skills including dynamic skills.

        Returns:
            List of ActiveSkill instances including base skills and dynamic skills
        """
        skills = list(self.active_skills)  # Copy base skills

        # Add Parallax skill dynamically if unit is adjacent to Market Futures anchor
        if hasattr(self, 'can_use_anchor') and self.can_use_anchor:
            # Import here to avoid circular imports
            from boneglaive.game.skills.delphic_appraiser import ParallaxSkill
            parallax_skill = ParallaxSkill()
            skills.append(parallax_skill)

        return skills

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
        ESTRANGE_STAT_PENALTY = -2
        PUMPED_UP_STAT_BONUS = 1

        estrange_penalty = ESTRANGE_STAT_PENALTY if self.estranged else 0

        pumped_up_bonus = 0
        if hasattr(self, 'pumped_up_active') and self.pumped_up_active:
            pumped_up_bonus = PUMPED_UP_STAT_BONUS

        # Shredded status overrides all defense bonuses to 0
        shredded_override = (hasattr(self, 'shredded') and self.shredded)

        # Calculate base stats with bonuses
        stats = {
            'hp': self.max_hp + self.hp_bonus + pumped_up_bonus,
            'attack': max(0 if self.type == UnitType.DERELICTIONIST else 1, self.attack + self.attack_bonus + estrange_penalty + pumped_up_bonus),
            'defense': 0 if shredded_override else max(0, self.defense + self.defense_bonus + estrange_penalty + pumped_up_bonus),
            'attack_range': max(1, self.attack_range + self.attack_range_bonus + estrange_penalty + pumped_up_bonus)
        }
        
        # Calculate base movement with bonuses
        base_movement = self.move_range + self.move_range_bonus + estrange_penalty
        
        # Add SEVERANCE status effect bonus (+1 movement)
        if hasattr(self, 'severance_active') and self.severance_active:
            base_movement += 1
        
        # Add Pumped Up status effect bonus to movement
        if hasattr(self, 'pumped_up_active') and self.pumped_up_active:
            base_movement += 1  # +1 movement
        
        # Seasonal bonuses are now applied as permanent bonuses when the game starts
        # (see _apply_seasonal_bonuses in engine.py)
        
        # Allow movement to be reduced to 0 or below by debuffs
        # Movement cannot go below 0 (cannot have negative movement)
        stats['move_range'] = max(0, base_movement)
        
        
        # If unit is a doppelganger (from Grae Exchange), set its attack to at least 2
        DOPPELGANGER_MIN_ATTACK = 2
        if self.is_doppelganger:
            halved_attack = stats['attack'] // 2
            stats['attack'] = max(DOPPELGANGER_MIN_ATTACK, halved_attack)
            # Echo cannot move
            stats['move_range'] = 0
            
        return stats
    
    def get_effective_prt(self):
        """Get effective PRT including bonuses from status effects."""
        effective_prt = self.prt + self.prt_bonus

        PUMPED_UP_PRT_BONUS = 1
        if hasattr(self, 'pumped_up_active') and self.pumped_up_active:
            effective_prt += PUMPED_UP_PRT_BONUS

        return effective_prt
        
    def get_type_name(self) -> str:
        """Get the unit's type name as a string."""
        return self.type.name

    def get_display_name(self, shortened=False, include_player=False) -> str:
        """Get the unit's display name.

        Args:
            shortened: If True, provides a shorter display name for UI menus
            include_player: If True, adds [P1]/[P2] suffix for combat log clarity
        """
        # Format unit type name for display (replace underscores with spaces)
        display_type = self.get_type_name()
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
                elif self.vapor_type == "CALIBRATION":
                    vapor_name = "CALIBRATION GAS"
                elif self.vapor_type == "LIVING_AEROSOL":
                    vapor_name = "LIVING AEROSOL"
                else:
                    vapor_name = "HEINOUS VAPOR"
                
                # Use vapor name
                if shortened:
                    base_name = vapor_name[:8]  # Shortened version
                else:
                    base_name = vapor_name

                # Add player designation if requested
                if include_player:
                    return f"{base_name} [P{self.player}]"
                else:
                    return base_name
            else:
                # Fallback case
                if include_player:
                    return f"HEINOUS VAPOR [P{self.player}]"
                else:
                    return "HEINOUS VAPOR"
        elif display_type == "FOWL_CONTRIVANCE":
            # Use a shorter name if requested (for UI menus)
            if shortened:
                display_type = "F.CONTRIV"
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
        elif display_type == "ORDNANCE_DRONE":
            # The ORDNANCE GRAFT's drone is displayed as QUADCOPTER (the enum keeps the
            # ORDNANCE_DRONE name for the sprite/internal wiring).
            display_type = "QUADCOPTER"

        # Any unit not special-cased above keeps its enum name; spaces in place of
        # underscores so multi-word types (e.g. ORDNANCE_GRAFT) read correctly.
        display_type = display_type.replace("_", " ")

        # For echo units, change name to "ECHO {TYPE}"
        if self.is_doppelganger:
            base_name = f"ECHO {display_type}"
        else:
            base_name = display_type

        # Add player designation if requested (for combat log)
        if include_player:
            return f"{base_name} [P{self.player}]"
        else:
            return base_name
    
    def apply_passive_skills(self, game=None, ui=None) -> None:
        """Apply effects of passive skills."""
        if self.passive_skill:
            self.passive_skill.apply_passive(self, game, ui)
            
    def is_immune_to_effects(self) -> bool:
        """Check if this unit has immunity to status effects and debuffs.
        Currently only GRAYMAN with Stasiality passive has this immunity.
        HEINOUS_VAPOR units are also immune to all status effects.
        Topiary units are immune while transformed (terrain form).
        Note: This includes immunity to physical traps like Viseroy."""
        # HEINOUS_VAPOR units are always immune to status effects
        if self.type == UnitType.HEINOUS_VAPOR:
            return True
        # GRAYMAN with Stasiality passive is immune
        if self.passive_skill and self.passive_skill.name == "Stasiality":
            return True
        # Topiary units are immune while transformed
        if hasattr(self, 'is_topiary') and self.is_topiary:
            return True
        return False

    def is_immune_to_trap(self) -> bool:
        """Check if this unit is immune to being trapped.
        GRAYMAN with Stasiality passive and HEINOUS_VAPOR units are immune to trapping effects."""
        # Use the general immunity check
        return self.is_immune_to_effects()
    
    def get_available_skills(self) -> List:
        """
        Get list of available active skills (not on cooldown and can be used).
        This filters out skills that require upgrades that aren't active.
        """
        available = []
        for skill in self.active_skills:
            if skill.current_cooldown == 0:
                # Check if skill requires an upgrade by trying can_use with no target
                # Skills that require upgrades will check in their can_use() method
                if skill.name == "Aerosolize Arms":
                    # Special check for Aerosolize Arms - only show if Effluvium Lathe is upgraded
                    from boneglaive.game.upgrades import UpgradeManager
                    if UpgradeManager.is_skill_upgraded(self, "Effluvium Lathe"):
                        available.append(skill)
                else:
                    # All other skills are available if not on cooldown
                    available.append(skill)
        return available
    
    def is_adjacent_to_upgraded_stasiality(self, game) -> bool:
        """
        Check if this unit is adjacent to an enemy GRAYMAN (or echo) with upgraded Stasiality.
        Used to determine if cooldowns should be frozen.
        """
        if not game:
            return False

        from boneglaive.utils.constants import UnitType
        from boneglaive.game.upgrades import UpgradeManager

        # Check all 8 adjacent tiles
        adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dy, dx in adjacent_offsets:
            adj_y = self.y + dy
            adj_x = self.x + dx

            # Check if position is valid
            if not game.is_valid_position(adj_y, adj_x):
                continue

            # Get unit at adjacent position
            adjacent_unit = game.get_unit_at(adj_y, adj_x)
            if not adjacent_unit:
                continue

            # Check if it's an enemy GRAYMAN (or echo) with upgraded Stasiality
            if (adjacent_unit.player != self.player and
                adjacent_unit.type == UnitType.GRAYMAN and
                adjacent_unit.is_alive() and
                UpgradeManager.is_skill_upgraded(adjacent_unit, "Stasiality")):
                return True

        return False

    def tick_cooldowns(self, game=None) -> None:
        """
        Reduce cooldowns for all skills by 1 turn.
        This is called at the end of a player's turn, only for that player's units.
        A skill with cooldown=1 can be used every turn, cooldown=2 every other turn, etc.
        Movement penalties are handled separately in reset_movement_penalty.

        If adjacent to an enemy GRAYMAN with upgraded Stasiality, cooldowns are frozen.
        """
        # Check if cooldowns are frozen by upgraded Stasiality
        if game and self.is_adjacent_to_upgraded_stasiality(game):
            return  # Don't tick cooldowns if adjacent to upgraded Stasiality

        # Tick skill cooldowns
        for skill in self.active_skills:
            skill.tick_cooldown()

        # Movement penalties are now handled in reset_movement_penalty method
    
    def can_move_to(self, y: int, x: int, game=None) -> bool:
        """
        Check if this unit can move to the specified position.
        FOWL_CONTRIVANCE units can only move along rail tiles.
        DERELICTIONIST with upgraded Severance can pass through furniture and terrain.
        """
        if not game:
            return True  # No game context, allow move

        # DERELICTIONIST with upgraded Severance can pass through furniture and terrain
        if self.type == UnitType.DERELICTIONIST:
            from boneglaive.game.upgrades import UpgradeManager
            if (UpgradeManager.is_skill_upgraded(self, "Severance") and
                hasattr(self, 'severance_active') and self.severance_active):
                # Can pass through all terrain types (furniture, pillars, walls, etc.)
                return True

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
    

    def deal_damage(self, damage: int, can_kill: bool = True) -> int:
        """Apply damage and return actual damage dealt (after PRT reduction)."""
        old_hp = self.hp
        if can_kill:
            self.hp = max(0, self.hp - damage)
        else:
            self.hp = max(1, self.hp - damage)
        return old_hp - self.hp

    def heal(self, heal_amount: int, source_description: str = "unknown source") -> int:
        """
        Apply healing to the unit with universal Auction Curse prevention.
        Returns the actual healing amount applied (0 if prevented).
        """
        if heal_amount <= 0:
            return 0

        # Check if healing is prevented by Auction Curse
        if hasattr(self, 'auction_curse_no_heal') and self.auction_curse_no_heal:
            from boneglaive.utils.message_log import message_log, MessageType
            message_log.add_message(
                f"{self.get_display_name()}'s healing is prevented by the curse",
                MessageType.WARNING,
                player=self.player
            )
            return 0

        # Topiary units cannot be healed (transformed into terrain)
        if hasattr(self, 'is_topiary') and self.is_topiary:
            return 0

        # Apply healing (don't exceed max HP)
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + heal_amount)
        return self.hp - old_hp

    def apply_shrapnel_damage(self, game=None) -> int:
        """
        Apply shrapnel damage at the start of turn if unit has embedded shrapnel.
        Returns the damage dealt.
        """
        if self.shrapnel_duration <= 0:
            return 0
            
        damage = 1  # Shrapnel always deals 1 damage
        actual_damage = self.deal_damage(damage)
        self.shrapnel_duration -= 1
        
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{self.get_display_name()} takes {actual_damage} damage from embedded shrapnel!",
            MessageType.ABILITY,
            player=self.player
        )
        
        return actual_damage
    
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
        self.attack_queued_from = None
        
        # Clear visual indicators
        self.vault_target_indicator = None
        self.site_inspection_indicator = None
        self.teleport_target_indicator = None
        self.expedite_path_indicator = None
        self.jawline_indicator = None
        
        self.action_timestamp = 0  # Reset the action timestamp
        
    def is_done_acting(self) -> bool:
        """Check if this unit has used an action that ends their turn (attack or skill)."""
        from boneglaive.utils.constants import UnitType
        
        # Attack always makes a unit done
        if self.attack_target is not None:
            return True
            
        # For skills, check unit type
        if self.skill_target is not None:
            # DERELICTIONIST can move after using a skill, so only done if they also have a move
            if self.type == UnitType.DERELICTIONIST:
                return self.move_target is not None  # Done only if skill + move
            else:
                return True  # All other units are done after skill
                
        return False  # No attack or skill = not done
    
        
    # HP property with invulnerability check
    @property
    def hp(self):
        return self._hp
        
    @hp.setter
    def hp(self, value):
        # Prevent infinite recursion during PRT damage processing
        if hasattr(self, '_applying_damage') and self._applying_damage:
            self._hp = value
            return
            
        # HEINOUS VAPOR units use PRT for effective invulnerability
        
        # Check if this is damage (HP reduction) and apply PRT
        if value < self._hp:
            # Reset PRT tracking at the start of damage processing
            self.last_prt_absorbed = 0
            # Calculate raw damage being attempted
            raw_damage = self._hp - value
            
            # CHECK FOR DISSOCIATION FIRST - before any damage processing
            if (hasattr(self, 'partition_shield_active') and self.partition_shield_active and
                self.prt > 0 and (self._hp - raw_damage) <= 0 and
                not getattr(self, 'partition_shield_blocked_fatal', False)):

                self.prt = INVULNERABLE_PRT
                self.partition_shield_blocked_fatal = True  # Mark for cleanup

                # Save caster reference for animation (before clearing it)
                self.partition_dissociation_caster = self.partition_shield_caster

                # Teleport DERELICTIONIST immediately
                if hasattr(self, 'partition_shield_caster') and self.partition_shield_caster and self._game:
                    self._game._teleport_derelictionist_away(self.partition_shield_caster, self, distance=4)
                
                # Apply derelicted immediately
                self.derelicted = True
                self.derelicted_duration = 1

                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"{self.get_display_name()} becomes anchored by abandonment",
                    MessageType.WARNING,
                    player=self.player
                )

                # Spawn building around the derelicted unit (only with Derelict upgrade)
                if self._game and self.partition_dissociation_caster:
                    from boneglaive.game.upgrades import UpgradeManager
                    if UpgradeManager.is_skill_upgraded(self.partition_dissociation_caster, "Derelict"):
                        from boneglaive.game.skills.derelictionist import _place_derelict_building
                        _place_derelict_building(self, self.partition_dissociation_caster, self._game, ui=None)
                
                # Remove partition shield status (keep INVULNERABLE_PRT until end of turn)
                self.partition_shield_active = False
                self.partition_shield_duration = 0

                # Increase PARTITION cooldown as penalty for dissociation
                # Base: 8 turns, Upgraded: 6 turns
                if self.partition_shield_caster:
                    from boneglaive.game.upgrades import UpgradeManager
                    is_upgraded = UpgradeManager.is_skill_upgraded(self.partition_shield_caster, "Partition")
                    dissociation_cooldown = 4 if is_upgraded else 6

                    for skill in self.partition_shield_caster.active_skills:
                        if hasattr(skill, 'name') and skill.name == "Partition":
                            skill.current_cooldown = dissociation_cooldown
                            from boneglaive.utils.debug import logger
                            logger.info(f"DISSOCIATION PENALTY: {self.partition_shield_caster.get_display_name()}'s Partition cooldown set to {dissociation_cooldown} ({'upgraded' if is_upgraded else 'base'})")
                            break
                
                self.partition_shield_caster = None
                self.partition_shield_emergency_active = False
                
                from boneglaive.utils.message_log import message_log, MessageType
                message_log.add_message(
                    f"{self.get_display_name()} dissociates from battle",
                    MessageType.ABILITY,
                    player=self.player
                )
                from boneglaive.utils.debug import logger
                logger.info(f"DISSOCIATION: {self.get_display_name()} prt boosted to 999, DERELICTIONIST teleported, unit derelicted")
                
                # Track PRT absorbed for message log correction (all damage absorbed by dissociation)
                self.last_prt_absorbed = raw_damage
                
                # Block this damage — all subsequent damage absorbed by INVULNERABLE_PRT
                self._applying_damage = True
                self._hp = self._hp  # No damage applied
                self._applying_damage = False
                return
            
            # Normal PRT processing if not fatal
            effective_prt = self.get_effective_prt()
            if effective_prt > 0:
                # Apply PRT reduction
                prt_absorbed = min(raw_damage, effective_prt)
                actual_damage = max(0, raw_damage - prt_absorbed)
                
                # Track PRT absorbed for message log correction
                self.last_prt_absorbed = prt_absorbed

                # Check for Demilune damage halving (after PRT)
                if (self._game and
                    hasattr(self._game, 'current_attacker') and
                    self._game.current_attacker and
                    hasattr(self._game.current_attacker, 'demilune_debuffed_by') and
                    self._game.current_attacker.demilune_debuffed_by and
                    self._game.current_attacker.demilune_debuffed_by == self):
                    # Attacker is debuffed by this POTPOURRIST - halve the damage
                    actual_damage = actual_damage // 2
                    from boneglaive.utils.debug import logger
                    logger.debug(f"DEMILUNE: {self._game.current_attacker.get_display_name()}'s damage halved by Demilune debuff ({actual_damage * 2} -> {actual_damage})")

                # Show partition message and animation for each attack (not just once per turn)
                if prt_absorbed > 0:
                    from boneglaive.utils.debug import logger
                    # Only show partition damage messages for Partition shields (not HEINOUS_VAPOR or topiary)
                    if self.type != UnitType.HEINOUS_VAPOR and not getattr(self, 'is_topiary', False):
                        from boneglaive.utils.message_log import message_log, MessageType
                        message_log.add_message(
                            f"{self.get_display_name()}'s partition takes #DAMAGE_{prt_absorbed}# damage",
                            MessageType.ABILITY,
                            player=self.player
                        )
                        logger.info(f"PRT AUTO: {self.get_display_name()}'s partition absorbed {prt_absorbed} damage")

                        # Signal for renderers to show partition hit animation
                        # Animation: detected by game_state.py and dispatched as AnimationEvent
                        self.partition_hit_for_animation = True
                    else:
                        # HEINOUS VAPOR units silently absorb damage as gas entities
                        logger.debug(f"HEINOUS VAPOR: {self.get_display_name()} silently absorbed {prt_absorbed} damage")
                
                # Apply final damage
                self._applying_damage = True
                old_hp = self._hp
                self._hp = max(0, self._hp - actual_damage)
                self._applying_damage = False

                # Check for death and award GP
                if old_hp > 0 and self._hp == 0:
                    self._handle_death()
            else:
                # No PRT - apply damage normally
                self.last_prt_absorbed = 0  # No PRT was applied

                # Check for Demilune damage halving (no PRT case)
                actual_damage = self._hp - value  # Calculate raw damage
                if (self._game and
                    hasattr(self._game, 'current_attacker') and
                    self._game.current_attacker and
                    hasattr(self._game.current_attacker, 'demilune_debuffed_by') and
                    self._game.current_attacker.demilune_debuffed_by and
                    self._game.current_attacker.demilune_debuffed_by == self):
                    # Attacker is debuffed by this POTPOURRIST - halve the damage
                    actual_damage = actual_damage // 2
                    from boneglaive.utils.debug import logger
                    logger.debug(f"DEMILUNE (no PRT): {self._game.current_attacker.get_display_name()}'s damage halved by Demilune debuff ({actual_damage * 2} -> {actual_damage})")

                # Apply the (possibly halved) damage
                self._applying_damage = True
                old_hp = self._hp
                self._hp = max(0, self._hp - actual_damage)
                self._applying_damage = False

                # Check for death and award GP
                if old_hp > 0 and self._hp == 0:
                    self._handle_death()
        else:
            # Normal HP setting (healing or non-damage changes)
            self.last_prt_absorbed = 0  # Clear PRT tracking for non-damage changes
            self._hp = value
            
    def expire(self):
        """Force unit expiration, bypassing invulnerability.
        Used when HEINOUS_VAPOR duration runs out."""
        self._hp = 0

    def _handle_death(self):
        """Handle unit death - award GP and create DeadUnit entry for respawn."""
        if not self._game:
            return

        from boneglaive.utils.constants import GP_ELIGIBLE_UNITS
        from boneglaive.game.engine import DeadUnit
        from boneglaive.utils.message_log import message_log, MessageType

        # Don't award GP for banished units (they will return)
        if hasattr(self, 'is_banished') and self.is_banished:
            return

        # Don't award GP for doppelgangers (they are temporary summons)
        if hasattr(self, 'is_doppelganger') and self.is_doppelganger:
            return

        # Check if this unit is GP-eligible (not a summon/echo)
        if self.type in GP_ELIGIBLE_UNITS:
            # Award GP to opposing player
            opposing_player = 2 if self.player == 1 else 1
            if opposing_player == 1:
                self._game.player1_gp += 1
                gp_total = self._game.player1_gp
            else:
                self._game.player2_gp += 1
                gp_total = self._game.player2_gp

            winner_name = self._game.get_player_name(opposing_player)

            # Log GP award
            message_log.add_message(
                f"{winner_name} scores 1 GP! ({gp_total}/{self._game.gp_win_threshold})",
                MessageType.SYSTEM,
                player=opposing_player
            )

            # Check if combined GP total crossed any upgrade point thresholds
            combined_gp = self._game.player1_gp + self._game.player2_gp
            for threshold in self._game.upgrade_point_thresholds:
                # Award points if threshold reached and not already processed
                if combined_gp >= threshold and threshold not in self._game.upgrade_points_awarded:
                    # Determine base UP and bonus UP for this threshold
                    if threshold == 2:
                        base_up = 2  # Everyone gets 2 UP
                        leader_bonus = 1  # Leader gets +1 bonus (3 total)
                    elif threshold == 4:
                        base_up = 1  # Everyone gets 1 UP
                        leader_bonus = 1  # Leader gets +1 bonus (2 total)
                    elif threshold == 6:
                        base_up = 1  # Everyone gets 1 UP
                        leader_bonus = 1  # Leader gets +1 bonus (2 total)
                    else:
                        continue  # Unknown threshold, skip

                    # Determine who's in the lead
                    if self._game.player1_gp > self._game.player2_gp:
                        leader = 1
                    elif self._game.player2_gp > self._game.player1_gp:
                        leader = 2
                    else:
                        leader = None  # Tied

                    # Award base UP to both players
                    self._game.player1_upgrade_points += base_up
                    self._game.player2_upgrade_points += base_up

                    # Award leader bonus if there's a leader
                    if leader == 1:
                        self._game.player1_upgrade_points += leader_bonus
                    elif leader == 2:
                        self._game.player2_upgrade_points += leader_bonus

                    # Mark threshold as processed
                    self._game.upgrade_points_awarded.add(threshold)

                    # Log upgrade point awards
                    player1_name = self._game.get_player_name(1)
                    player2_name = self._game.get_player_name(2)

                    if leader == 1:
                        message_log.add_message(
                            f"Combined GP reached {threshold}! {player1_name} earns {base_up + leader_bonus} UP (leading), {player2_name} earns {base_up} UP",
                            MessageType.SYSTEM
                        )
                    elif leader == 2:
                        message_log.add_message(
                            f"Combined GP reached {threshold}! {player2_name} earns {base_up + leader_bonus} UP (leading), {player1_name} earns {base_up} UP",
                            MessageType.SYSTEM
                        )
                    else:
                        # Tied
                        message_log.add_message(
                            f"Combined GP reached {threshold}! Both players earn {base_up} UP (tied)",
                            MessageType.SYSTEM
                        )

            # Handle Dominion death penalty mitigation (manual upgrade) for MARROW_CONDENSER
            dominion_kills = 0
            dominion_skill_states = {}

            if self.type == UnitType.MARROW_CONDENSER and hasattr(self, 'passive_skill'):
                from boneglaive.game.upgrades import UpgradeManager
                if UpgradeManager.is_skill_upgraded(self, "Dominion"):
                    passive = self.passive_skill
                    if passive.name == "Dominion" and passive.kills > 0:
                        # Decrement kills by 1 (lose current stage only)
                        new_kills = passive.kills - 1
                        dominion_kills = new_kills

                        # Determine which skill to downgrade (reverse order: bone_tithe → ossify → marrow_dike)
                        downgraded_skill = None
                        if passive.bone_tithe_upgraded:
                            downgraded_skill = "bone_tithe"
                            passive.bone_tithe_upgraded = False
                            passive.available_upgrades.append("bone_tithe")
                        elif passive.ossify_upgraded:
                            downgraded_skill = "ossify"
                            passive.ossify_upgraded = False
                            passive.available_upgrades.append("ossify")
                        elif passive.marrow_dike_upgraded:
                            downgraded_skill = "marrow_dike"
                            passive.marrow_dike_upgraded = False
                            passive.available_upgrades.append("marrow_dike")

                        # Store skill states for respawn
                        dominion_skill_states = {
                            'marrow_dike': passive.marrow_dike_upgraded,
                            'ossify': passive.ossify_upgraded,
                            'bone_tithe': passive.bone_tithe_upgraded
                        }

                        # Log the downgrade
                        if downgraded_skill:
                            message_log.add_message(
                                f"{self.get_display_name()} loses Dominion upgrade: {downgraded_skill}",
                                MessageType.SYSTEM,
                                player=self.player
                            )

            # Create DeadUnit entry for respawn
            # Preserve upgraded_skills for respawn
            upgraded_skills_copy = set(self.upgraded_skills) if hasattr(self, 'upgraded_skills') else set()
            # Preserve Dominion manual upgrade attack bonuses for MARROW_CONDENSER (old system - deprecated)
            dominion_attack = getattr(self, 'dominion_permanent_attack', 0)
            dead_unit = DeadUnit(
                unit_type=self.type,
                player=self.player,
                death_turn=self._game.turn,
                greek_id=self.greek_id,
                upgraded_skills=upgraded_skills_copy,
                dominion_permanent_attack=dominion_attack,
                dominion_kills=dominion_kills,
                dominion_skill_states=dominion_skill_states
            )
            self._game.dead_units.append(dead_unit)

            # Remove from active units list
            if self in self._game.units:
                self._game.units.remove(self)
                # CRITICAL: Remove from spatial grid
                self._game._remove_from_unit_grid(self)

            logger.info(f"GP SYSTEM: {self.get_display_name()} died, {winner_name} awarded 1 GP ({gp_total}/{self._game.gp_win_threshold})")
        else:
            # Summon/echo death - no GP awarded, no respawn
            logger.info(f"GP SYSTEM: {self.get_display_name()} (summon/echo) died - no GP awarded")

    # Position properties with trap release functionality
    @property
    def y(self):
        return self._y
        
    @y.setter
    def y(self, value):
        # Store old position for trap checks and spatial grid updates
        old_y = self._y

        # Update position
        self._y = value

        # Only check if position actually changed and game reference exists
        if old_y != value and self._game:
            # OPTIMIZATION: Update spatial grid
            self._game._update_unit_grid(self, old_y, self._x)

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
        # Store old position for trap checks and spatial grid updates
        old_x = self._x

        # Update position
        self._x = value

        # Only check if position actually changed and game reference exists
        if old_x != value and self._game:
            # OPTIMIZATION: Update spatial grid
            self._game._update_unit_grid(self, self._y, old_x)

            # Case 1: If this is a MANDIBLE_FOREMAN, check for trap release
            if self.type == UnitType.MANDIBLE_FOREMAN:
                self._game._check_position_change_trap_release(self, self._y, old_x)

            # Case 2: If this unit is trapped, check for trap release
            if self.trapped_by is not None:
                self._game._check_position_change_trap_release(self, self._y, old_x)
    
    def set_game_reference(self, game):
        """Set reference to the game for trap checks and register in spatial grid."""
        self._game = game
        # Add unit to spatial grid now that we have game reference
        if game and self.is_alive():
            game._update_unit_grid(self)

    def set_position_atomic(self, y: int, x: int) -> bool:
        """
        Atomically set unit position to (y, x).
        This prevents intermediate position collisions that can occur when setting y and x separately.

        Returns:
            True if position was set successfully, False if blocked by collision
        """
        from boneglaive.utils.debug import logger

        if not self._game:
            # No game reference, just set directly
            self._y = y
            self._x = x
            return True

        # Check if intermediate position (new_y, old_x) would collide
        if y != self._y:  # Y is changing
            intermediate_unit = self._game.get_unit_at(y, self._x)
            if intermediate_unit is not None and intermediate_unit != self:
                logger.error(f"Cannot move {self.get_display_name()} to ({y}, {x}) - intermediate position ({y}, {self._x}) occupied by {intermediate_unit.get_display_name()}")
                return False

        # Check if final position would collide
        final_unit = self._game.get_unit_at(y, x)
        if final_unit is not None and final_unit != self:
            logger.error(f"Cannot move {self.get_display_name()} to ({y}, {x}) - position occupied by {final_unit.get_display_name()}")
            return False

        # Safe to move - use property setters (they handle grid updates)
        self.y = y
        self.x = x
        return True

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

        # NOTE: Jawline duration is now decremented in Game.execute_turn
        # to ensure it only happens on the player's own turn

        # Handle base Pry status effect duration - BEFORE resetting move_range_bonus
        if hasattr(self, 'pry_duration') and self.pry_duration > 0:
            # Decrement the duration
            self.pry_duration -= 1

            # If duration expired, clear the effect and restore move penalty
            if self.pry_duration <= 0:
                self.was_pried = False
                self.pry_active = False
                self.move_range_bonus += 1  # Restore the -1 penalty
                if hasattr(self, 'pry_duration'):
                    delattr(self, 'pry_duration')
                if hasattr(self, 'pry_penalty_amount'):
                    delattr(self, 'pry_penalty_amount')
        # Handle upgraded Pry status effect duration
        elif hasattr(self, 'pry_upgraded_duration') and self.pry_upgraded_duration > 0:
            # Decrement the duration
            self.pry_upgraded_duration -= 1

            # If duration expired, clear the effect and restore move penalty
            if self.pry_upgraded_duration <= 0:
                self.was_pried_upgraded = False
                self.pry_active = False
                self.move_range_bonus += 2  # Restore the -2 penalty
                if hasattr(self, 'pry_upgraded_duration'):
                    delattr(self, 'pry_upgraded_duration')
                if hasattr(self, 'pry_upgraded_penalty_amount'):
                    delattr(self, 'pry_upgraded_penalty_amount')
        # For backward compatibility - reset was_pried if no duration
        elif self.was_pried:
            self.was_pried = False
            if hasattr(self, 'pry_active'):
                self.pry_active = False
            self.move_range_bonus += 1
        elif self.was_pried_upgraded:
            self.was_pried_upgraded = False
            if hasattr(self, 'pry_active'):
                self.pry_active = False
            # Clear movement penalty for legacy upgraded Pry effects
            if self.move_range_bonus < 0:
                self.move_range_bonus = 0
        # Do not reset move_range_bonus if affected by Jawline, Pry, or Ossify
        elif (not self.jawline_affected and
              not self.was_pried and
              not self.was_pried_upgraded and
              not (hasattr(self, 'ossify_active') and self.ossify_active) and
              self.move_range_bonus < 0):
            self.move_range_bonus = 0
                
    def apply_vapor_effects(self, game: 'Game', ui=None) -> None:
        """
        Apply area effects for HEINOUS_VAPOR units.
        This is called during combat phase processing.
        Note: The game engine only calls this method for vapors belonging to the current player.
        """
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        
        # Only process if this is a HEINOUS_VAPOR
        if self.type != UnitType.HEINOUS_VAPOR or not hasattr(self, 'vapor_type') or not self.vapor_type:
            return

        # LIVING_AEROSOL does not produce gas clouds
        if self.vapor_type == "LIVING_AEROSOL":
            return

        # Define the 3x3 area around the vapor
        affected_area = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                ny, nx = self.y + dy, self.x + dx
                if game.is_valid_position(ny, nx):
                    affected_area.append((ny, nx))
                    
        # Queue graphical animation if available
        if ui and hasattr(ui, 'game_adapter') and hasattr(ui.game_adapter, 'queue_vapor_aoe_tick'):
            # Graphical mode - queue AOE tick animation
            ui.game_adapter.queue_vapor_aoe_tick(self)

        
        # Find units in the affected area
        affected_units = []
        for pos in affected_area:
            y, x = pos
            unit = game.get_unit_at(y, x)
            if unit and unit.is_alive():
                affected_units.append(unit)
                
        # Process effects based on vapor type
        if self.vapor_type == "BROACHING":
            # Broaching Gas: Damages enemies (1 damage base, +3 if upgraded) and cleanses allies of status effects

            # Check if Broaching Gas is upgraded (increased damage by +3)
            from boneglaive.game.upgrades import UpgradeManager
            is_upgraded = False
            if hasattr(self, 'vapor_creator') and self.vapor_creator:
                is_upgraded = UpgradeManager.is_skill_upgraded(self.vapor_creator, "Broaching Gas")

            for unit in affected_units:
                if unit.player != self.player:
                    # Enemy unit - apply damage
                    if is_upgraded:
                        damage = 4  # Upgraded: 1 + 3 = 4 damage (reduced by defense)
                    else:
                        damage = 1  # Base: 1 damage (reduced by defense)

                    previous_hp = unit.hp

                    # Normal damage (defense applies via HP setter)
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
                    # Ally unit - cleanse ONE random negative status effect
                    import random

                    # Build list of available effects to cleanse (name, clear_function pairs)
                    available_effects = []

                    # Derelicted
                    if hasattr(unit, 'derelicted') and unit.derelicted:
                        def clear_derelicted():
                            unit.derelicted = False
                            if hasattr(unit, 'derelicted_duration'):
                                unit.derelicted_duration = 0
                        available_effects.append(("Derelicted", clear_derelicted))

                    # Estrangement
                    if hasattr(unit, 'estranged') and unit.estranged:
                        def clear_estranged():
                            unit.estranged = False
                            # Restore original max HP if it was reduced by upgraded Estrange
                            if hasattr(unit, 'estranged_original_max_hp'):
                                unit.max_hp = unit.estranged_original_max_hp
                                delattr(unit, 'estranged_original_max_hp')
                        available_effects.append(("Estrangement", clear_estranged))

                    # Pry movement penalty (base or upgraded)
                    if hasattr(unit, 'was_pried') and unit.was_pried:
                        def clear_pry():
                            unit.was_pried = False
                            if hasattr(unit, 'pry_active'):
                                unit.pry_active = False
                            # Restore movement by removing the stored penalty (same as Vagal Run fix)
                            if hasattr(unit, 'pry_penalty_amount'):
                                unit.move_range_bonus -= unit.pry_penalty_amount  # pry_penalty_amount is negative
                                delattr(unit, 'pry_penalty_amount')
                            if hasattr(unit, 'pry_duration'):
                                unit.pry_duration = 0
                        available_effects.append(("Pry movement penalty", clear_pry))
                    elif hasattr(unit, 'was_pried_upgraded') and unit.was_pried_upgraded:
                        def clear_pry_upgraded():
                            unit.was_pried_upgraded = False
                            if hasattr(unit, 'pry_active'):
                                unit.pry_active = False
                            # Restore movement by removing the stored upgraded penalty
                            if hasattr(unit, 'pry_upgraded_penalty_amount'):
                                unit.move_range_bonus -= unit.pry_upgraded_penalty_amount
                                delattr(unit, 'pry_upgraded_penalty_amount')
                            if hasattr(unit, 'pry_upgraded_duration'):
                                unit.pry_upgraded_duration = 0
                        available_effects.append(("Pry movement penalty (upgraded)", clear_pry_upgraded))

                    # Jawline immobilization
                    if hasattr(unit, 'jawline_affected') and unit.jawline_affected:
                        def clear_jawline():
                            unit.jawline_affected = False
                            if hasattr(unit, 'jawline_duration'):
                                unit.jawline_duration = 0
                            # Restore the actual penalty that was applied
                            if hasattr(unit, 'jawline_original_move'):
                                unit.move_range_bonus += unit.jawline_original_move
                        available_effects.append(("Jawline immobilization", clear_jawline))

                    # Recharging
                    if hasattr(unit, 'gaussian_dusk_recharge') and unit.gaussian_dusk_recharge > 0:
                        def clear_recharging():
                            unit.gaussian_dusk_recharge = 0
                        available_effects.append(("Recharging", clear_recharging))

                    # Imbued
                    if hasattr(unit, 'status_imbued') and unit.status_imbued:
                        def clear_imbued():
                            unit.status_imbued = False
                            if hasattr(unit, 'status_imbued_duration'):
                                unit.status_imbued_duration = 0
                            if hasattr(unit, 'status_imbued_player'):
                                unit.status_imbued_player = None
                            if hasattr(unit, 'status_imbued_cosmic_value'):
                                unit.status_imbued_cosmic_value = None
                        available_effects.append(("Imbued", clear_imbued))

                    # Trapped
                    if hasattr(unit, 'trapped_by') and unit.trapped_by:
                        def clear_trapped():
                            unit.trapped_by = None
                            if hasattr(unit, 'trap_duration'):
                                unit.trap_duration = 0
                        available_effects.append(("Trapped", clear_trapped))

                    # Mired
                    if hasattr(unit, 'mired') and unit.mired:
                        def clear_mired():
                            unit.mired = False
                            if hasattr(unit, 'mired_duration'):
                                unit.mired_duration = 0
                            # Restore the penalties that were applied by mired (-1 attack, -1 move)
                            unit.attack_bonus += 1
                            unit.move_range_bonus += 1
                        available_effects.append(("Mired", clear_mired))

                    # Neural Shunt
                    if hasattr(unit, 'neural_shunt_affected') and unit.neural_shunt_affected:
                        def clear_neural_shunt():
                            unit.neural_shunt_affected = False
                            if hasattr(unit, 'neural_shunt_duration'):
                                unit.neural_shunt_duration = 0
                        available_effects.append(("Neural Shunt", clear_neural_shunt))

                    # Auction Curse
                    if hasattr(unit, 'auction_curse_dot') and unit.auction_curse_dot:
                        def clear_auction_curse():
                            unit.auction_curse_dot = False
                        available_effects.append(("Auction Curse", clear_auction_curse))

                    # RF Burn
                    if hasattr(unit, 'radiation_stacks') and unit.radiation_stacks:
                        if isinstance(unit.radiation_stacks, list):
                            if len(unit.radiation_stacks) > 0:
                                def clear_radiation():
                                    unit.radiation_stacks = []
                                available_effects.append(("RF Burn", clear_radiation))
                        else:
                            if unit.radiation_stacks > 0:
                                def clear_radiation():
                                    unit.radiation_stacks = 0
                                available_effects.append(("RF Burn", clear_radiation))

                    # Shrapnel
                    if hasattr(unit, 'shrapnel_duration') and unit.shrapnel_duration > 0:
                        def clear_shrapnel():
                            unit.shrapnel_duration = 0
                        available_effects.append(("Shrapnel", clear_shrapnel))

                    # Disarmed
                    if hasattr(unit, 'status_disarmed') and unit.status_disarmed:
                        def clear_disarmed():
                            unit.status_disarmed = False
                            if hasattr(unit, 'status_disarmed_duration'):
                                unit.status_disarmed_duration = 0
                        available_effects.append(("Disarmed", clear_disarmed))

                    # Selenic Backdraft
                    if hasattr(unit, 'selenic_backdraft') and unit.selenic_backdraft:
                        def clear_selenic():
                            unit.selenic_backdraft = False
                            unit.selenic_backdraft_by = None
                            unit.selenic_backdraft_duration = 0
                        available_effects.append(("Selenic Backdraft", clear_selenic))

                    # Topiary
                    if hasattr(unit, 'is_topiary') and unit.is_topiary:
                        def clear_topiary():
                            from boneglaive.game.map import TerrainType
                            unit.is_topiary = False
                            unit.topiary_duration = 0
                            if hasattr(unit, 'topiary_original_prt'):
                                unit.prt = unit.topiary_original_prt
                                delattr(unit, 'topiary_original_prt')
                            # Clear topiary terrain at unit's position
                            if game.map.get_terrain_at(unit.y, unit.x) == TerrainType.TOPIARY:
                                game.map.set_terrain_at(unit.y, unit.x, TerrainType.EMPTY)
                            # Remove from topiary_units tracking
                            if hasattr(game, 'topiary_units') and (unit.y, unit.x) in game.topiary_units:
                                del game.topiary_units[(unit.y, unit.x)]
                            # Clean up cosmic values at this position
                            for player_id in list(game.map.cosmic_values.keys()):
                                if (unit.y, unit.x) in game.map.cosmic_values[player_id]:
                                    del game.map.cosmic_values[player_id][(unit.y, unit.x)]
                        available_effects.append(("Topiary", clear_topiary))

                    # Bombs (ORDNANCE GRAFT). Drip-cleanse peels ONE bomb, not the
                    # whole cluster — Bomb counts as a single peelable category here, so
                    # a stacked target is no likelier to be hit than any other debuff.
                    if getattr(unit, 'bombs', None):
                        def clear_one_bomb():
                            from boneglaive.game.skills.ordnance_graft import remove_one_bomb
                            remove_one_bomb(unit)
                        available_effects.append(("a bomb", clear_one_bomb))

                    # If any effects are available, randomly pick ONE to cleanse
                    if available_effects:
                        effect_name, clear_function = random.choice(available_effects)
                        clear_function()

                        # Log the single cleansed effect
                        message_log.add_message(
                            f"{unit.get_display_name()} is cleansed of {effect_name}!",
                            MessageType.ABILITY,
                            player=self.player
                        )

                    
        elif self.vapor_type == "SAFETY":
            # Saft-E-Gas performs two functions:
            # 1. Protection zone: Always active, prevents targeting of allied units inside
            # 2. Healing: Heals allies by 1 HP per tick

            # Grab reference to game for debugging
            game = self._game

            # Check if Saft-E-Gas is upgraded (grants PRT instead of DEF)
            from boneglaive.game.upgrades import UpgradeManager
            is_upgraded = False
            if hasattr(self, 'vapor_creator') and self.vapor_creator:
                is_upgraded = UpgradeManager.is_skill_upgraded(self.vapor_creator, "Saft-E-Gas")

            # First, find all units that were previously protected by this vapor but are no longer in range
            # We need to clean up their protection lists
            for game_unit in game.units:
                if (game_unit.is_alive() and
                    hasattr(game_unit, 'protected_by_safety_gas') and
                    game_unit.protected_by_safety_gas and
                    self in game_unit.protected_by_safety_gas and
                    game_unit not in affected_units):

                    # Unit is no longer affected by this vapor - remove protection bonus
                    game_unit.protected_by_safety_gas.remove(self)
                    if is_upgraded:
                        game_unit.prt_bonus -= 1
                        logger.debug(f"{game_unit.get_display_name()} loses +1 PRT from {self.get_display_name()} (moved out of range)")
                    else:
                        game_unit.defense_bonus -= 1
                        logger.debug(f"{game_unit.get_display_name()} loses +1 defense from {self.get_display_name()} (moved out of range)")

                    # If there are no more protecting vapors, clean up the attribute
                    if not game_unit.protected_by_safety_gas:
                        logger.debug(f"{game_unit.get_display_name()} is no longer protected by any safety gas")
                        delattr(game_unit, 'protected_by_safety_gas')
                    # Double check - ensure the protecting vapor is actually in the game
                    elif hasattr(game, 'units') and self not in game.units:
                        if self in game_unit.protected_by_safety_gas:
                            game_unit.protected_by_safety_gas.remove(self)
                            if is_upgraded:
                                game_unit.prt_bonus -= 1
                                logger.debug(f"{game_unit.get_display_name()} loses +1 PRT from removed vapor")
                            else:
                                game_unit.defense_bonus -= 1
                                logger.debug(f"{game_unit.get_display_name()} loses +1 defense from removed vapor")
                            # If there are no more protecting vapors after this, clean up the attribute
                            if not game_unit.protected_by_safety_gas:
                                delattr(game_unit, 'protected_by_safety_gas')

            # STAT BOOST EFFECT: Grant +1 PRT (upgraded) or +1 DEF (base) to all allied units in the cloud
            for unit in affected_units:
                if unit.player == self.player and unit != self:
                    # Set a property on the unit to mark it as protected by safety gas
                    if not hasattr(unit, 'protected_by_safety_gas'):
                        unit.protected_by_safety_gas = []
                        logger.debug(f"{unit.get_display_name()} gains +1 defense from first safety gas")
                    if self not in unit.protected_by_safety_gas:
                        unit.protected_by_safety_gas.append(self)
                        # Apply stat bonus based on upgrade
                        if is_upgraded:
                            unit.prt_bonus += 1
                        else:
                            unit.defense_bonus += 1
                        logger.debug(f"{unit.get_display_name()} gains +1 defense from safety gas from {self.get_display_name()}")
            
            # HEALING EFFECT: Heal allied units in the cloud
            for unit in affected_units:
                if unit.player == self.player and unit != self and unit.hp < unit.max_hp:
                    # Heal ally unit using universal heal method
                    # Upgraded: 2 HP per tick, Base: 1 HP per tick
                    healing = 2 if is_upgraded else 1
                    actual_heal = unit.heal(healing, "HEINOUS VAPOR healing")

                    # Log healing only if it actually occurred
                    if actual_heal > 0:
                        message_log.add_message(
                            f"{self.get_display_name()} heals {unit.get_display_name()} for {actual_heal} HP",
                        MessageType.ABILITY,
                        player=self.player
                    )
                    
                            
        elif self.vapor_type == "COOLANT":
            # Coolant Gas: Heals allies by 3 HP
            for unit in affected_units:
                if unit.player == self.player and unit != self and unit.hp < unit.max_hp:
                    # Heal ally unit using universal heal method
                    healing = 3
                    actual_heal = unit.heal(healing, "Coolant Gas healing")

                    # Log healing only if it actually occurred
                    if actual_heal > 0:
                        message_log.add_message(
                            f"{self.get_display_name()} heals {unit.get_display_name()} for {actual_heal} HP",
                        MessageType.ABILITY,
                        player=self.player
                    )
                    
                            
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
                    
                        
                    # Check if unit was defeated
                    if unit.hp <= 0:
                        message_log.add_message(
                            f"{unit.get_display_name()} perishes!",
                            MessageType.COMBAT,
                            player=self.player,
                            target=unit.player,
                            target_name=unit.get_display_name()
                        )

        elif self.vapor_type == "CALIBRATION":
            # Calibration Gas: Temporarily resets all units (allies and enemies) to base stats

            # Grab reference to game
            game = self._game

            # First, restore stats for units that left the calibration cloud
            for game_unit in game.units:
                if (game_unit.is_alive() and
                    hasattr(game_unit, 'calibrated_by') and
                    self in game_unit.calibrated_by and
                    game_unit not in affected_units):

                    # Unit left the vapor - restore their original stat bonuses
                    game_unit.calibrated_by.remove(self)

                    # Restore saved bonuses
                    if hasattr(game_unit, 'pre_calibration_stats'):
                        saved_stats = game_unit.pre_calibration_stats.get(self, {})
                        game_unit.attack_bonus = saved_stats.get('attack_bonus', 0)
                        game_unit.defense_bonus = saved_stats.get('defense_bonus', 0)
                        game_unit.move_range_bonus = saved_stats.get('move_range_bonus', 0)
                        game_unit.attack_range_bonus = saved_stats.get('attack_range_bonus', 0)
                        game_unit.prt_bonus = saved_stats.get('prt_bonus', 0)

                        # Clean up the saved stats for this vapor
                        del game_unit.pre_calibration_stats[self]
                        if not game_unit.pre_calibration_stats:
                            delattr(game_unit, 'pre_calibration_stats')

                        logger.debug(f"{game_unit.get_display_name()} stats restored after leaving Calibration Gas")

                    # Clean up the calibrated_by list
                    if not game_unit.calibrated_by:
                        delattr(game_unit, 'calibrated_by')

            # Apply normalization to units currently in the cloud
            for unit in affected_units:
                if unit != self:  # Don't affect self (the vapor)
                    # Track if this unit is newly affected by this vapor
                    if not hasattr(unit, 'calibrated_by'):
                        unit.calibrated_by = []

                    if self not in unit.calibrated_by:
                        # First time this vapor is affecting this unit - save current stats
                        unit.calibrated_by.append(self)

                        if not hasattr(unit, 'pre_calibration_stats'):
                            unit.pre_calibration_stats = {}

                        # Save current stat bonuses before normalization
                        unit.pre_calibration_stats[self] = {
                            'attack_bonus': unit.attack_bonus,
                            'defense_bonus': unit.defense_bonus,
                            'move_range_bonus': unit.move_range_bonus,
                            'attack_range_bonus': unit.attack_range_bonus,
                            'prt_bonus': unit.prt_bonus
                        }

                        # Check if any stats will be reset
                        stats_reset = []
                        if unit.attack_bonus != 0:
                            stats_reset.append("ATK")
                        if unit.defense_bonus != 0:
                            stats_reset.append("DEF")
                        if unit.move_range_bonus != 0:
                            stats_reset.append("MOVE")
                        if unit.attack_range_bonus != 0:
                            stats_reset.append("RANGE")
                        if unit.prt_bonus != 0:
                            stats_reset.append("PRT")

                        # Reset all stat bonuses to 0
                        unit.attack_bonus = 0
                        unit.defense_bonus = 0
                        unit.move_range_bonus = 0
                        unit.attack_range_bonus = 0
                        unit.prt_bonus = 0

                        # Log normalization if any stats were reset
                        if stats_reset:
                            message_log.add_message(
                                f"{unit.get_display_name()} is normalized by Calibration Gas",
                                MessageType.WARNING,
                                player=self.player
                            )
                            logger.debug(f"{unit.get_display_name()} normalized by Calibration Gas")

    
    def apply_radiation_damage(self, game: 'Game', ui=None) -> int:
        """
        Apply radiation damage from all active radiation stacks.
        Returns total damage dealt.
        """
        if not hasattr(self, 'radiation_stacks') or not self.radiation_stacks:
            return 0

        # GRAYMAN with Stasiality is immune to radiation
        if self.is_immune_to_effects():
            # Clear all radiation stacks
            self.radiation_stacks = []
            return 0

        total_damage = len(self.radiation_stacks)  # 1 damage per stack
        if total_damage <= 0:
            return 0
            
        # Apply damage
        self.hp = max(0, self.hp - total_damage)
        
        # Log radiation damage
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{self.get_display_name()} suffers {total_damage} RF burn damage",
            MessageType.ABILITY,
            player=self.player
        )
        
        
        # Decrement all radiation stack durations
        self.radiation_stacks = [duration - 1 for duration in self.radiation_stacks if duration > 1]
        
        return total_damage
    
    def is_untargetable(self) -> bool:
        """Check if this unit is untargetable due to status effects."""
        # Units under Karrier Rave are untargetable
        if hasattr(self, 'carrier_rave_active') and self.carrier_rave_active:
            return True
            
        return False
    
    def can_be_targeted_by(self, attacker) -> bool:
        """Check if this unit can be targeted by a specific attacker."""
        # First check if this unit is globally untargetable
        if self.is_untargetable():
            return False
        
        # Units under KARRIER_RAVE cannot be targeted by enemy units
        if (hasattr(self, 'carrier_rave_active') and self.carrier_rave_active and 
            attacker.player != self.player):
            return False
            
        return True
    
    def process_interferer_effects(self, game: 'Game') -> None:
        """Process INTERFERER-specific status effects at end of turn."""
        # Karrier Rave duration is now processed at the end of execute_turn (after combat)
        # to prevent it from expiring before the attack executes

        # Neural Shunt duration is now processed at the end of execute_turn (after random actions)
        # to prevent it from expiring before the random actions are applied
        
    def get_skill_by_key(self, key: str) -> Optional:
        """Get an active skill by its key (for UI selection)."""
        key = key.upper()
        for skill in self.active_skills:
            if skill.key.upper() == key:
                return skill
        return None
        
    
    def _teleport_derelictionist_away(self, derelictionist):
        """Helper method to teleport DERELICTIONIST to random valid position 3+ tiles away."""
        if not hasattr(self, '_game') or not self._game:
            return
            
        game = self._game
        valid_positions = []
        
        # Find all valid positions 3+ tiles away
        for y in range(game.map.height):
            for x in range(game.map.width):
                if (game.is_valid_position(y, x) and 
                    game.map.is_passable(y, x) and
                    game.get_unit_at(y, x) is None):
                    
                    # Calculate distance from protected unit
                    distance = abs(y - self.y) + abs(x - self.x)
                    if distance >= 3:
                        valid_positions.append((y, x))
        
        if valid_positions:
            import random
            new_y, new_x = random.choice(valid_positions)
            derelictionist.y = new_y
            derelictionist.x = new_x
            
            from boneglaive.utils.message_log import message_log, MessageType
            message_log.add_message(
                f"{derelictionist.get_display_name()} dissociates away from the trauma!",
                MessageType.ABILITY
            )
    
    def _trigger_abreaction(self):
        """Trigger trauma processing abreaction - deal trauma debt, heal, cleanse."""
        if not hasattr(self, 'trauma_processing_active') or not self.trauma_processing_active:
            return
            
        from boneglaive.utils.debug import logger
        from boneglaive.utils.message_log import message_log, MessageType
        from boneglaive.game.skills.derelictionist import calculate_distance
        
        caster = getattr(self, 'trauma_processing_caster', None)
        trauma_damage = self.trauma_debt
        
        # Deal stored trauma damage
        if trauma_damage > 0:
            previous_hp = self.hp
            self.hp = max(0, self.hp - trauma_damage)
            actual_trauma_damage = previous_hp - self.hp
            
            message_log.add_message(
                f"{self.get_display_name()} experiences abreaction ({actual_trauma_damage} trauma damage)!",
                MessageType.COMBAT
            )
        
        # Calculate healing based on distance from DERELICTIONIST
        heal_amount = trauma_damage  # Base healing equals trauma damage
        if caster and caster.is_alive():
            distance = calculate_distance(caster, self)
            heal_amount += distance  # Add distance bonus
        
        # Apply healing
        if heal_amount > 0 and self.hp < self.max_hp:
            # Apply healing using universal heal method
            actual_heal = self.heal(heal_amount, "processed trauma")

            if actual_heal > 0:
                message_log.add_message(
                    f"{self.get_display_name()} heals for {actual_heal} HP from processed trauma!",
                    MessageType.ABILITY
                )
            
        # Remove ALL negative status effects (cleanse)
        self._cleanse_all_negative_effects()
        
        # Remove trauma processing status and attack bonus
        self.trauma_processing_active = False
        self.trauma_processing_caster = None
        self.trauma_debt = 0
        self.attack_bonus -= 3  # Remove the +3 attack bonus
        
        message_log.add_message(
            f"{self.get_display_name()}'s trauma processing ends - all ailments cleansed!",
            MessageType.ABILITY
        )
        
        logger.info(f"ABREACTION: {self.get_display_name()} healed {heal_amount}, cleansed, lost attack bonus")
    
    def _cleanse_all_negative_effects(self):
        """Remove all negative status effects from the unit."""
        # Reverse stat modifications before clearing flags
        if hasattr(self, 'mired') and self.mired:
            self.attack_bonus += 1  # Mired applies -1 attack
            self.move_range_bonus += 1  # Mired applies -1 move

        if hasattr(self, 'jawline_affected') and self.jawline_affected:
            if hasattr(self, 'jawline_original_move'):
                self.move_range_bonus += self.jawline_original_move
                delattr(self, 'jawline_original_move')

        if hasattr(self, 'estranged') and self.estranged:
            if hasattr(self, 'estranged_original_max_hp'):
                self.max_hp = self.estranged_original_max_hp
                delattr(self, 'estranged_original_max_hp')

        # Reverse Pry movement penalty
        if hasattr(self, 'was_pried_upgraded') and self.was_pried_upgraded:
            self.move_range_bonus += 2
        elif hasattr(self, 'was_pried') and self.was_pried:
            self.move_range_bonus += 1

        # List of negative status effects to cleanse
        negative_effects = [
            'estranged', 'mired', 'jawline_affected', 'neural_shunt_affected',
            'derelicted', 'was_pried', 'was_pried_upgraded', 'pry_active'
        ]

        # Reset negative status effects
        for effect in negative_effects:
            if hasattr(self, effect):
                setattr(self, effect, False)

        # Reset duration counters
        duration_counters = [
            'estranged_duration', 'mired_duration', 'jawline_duration',
            'neural_shunt_duration', 'derelicted_duration',
            'pry_upgraded_duration'
        ]

        for counter in duration_counters:
            if hasattr(self, counter):
                setattr(self, counter, 0)

        # Clear radiation stacks
        if hasattr(self, 'radiation_stacks'):
            self.radiation_stacks = []

        # Clear ORDNANCE GRAFT bombs (a full cleanse defuses the whole cluster).
        if getattr(self, 'bombs', None):
            self.bombs.clear()