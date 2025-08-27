#!/usr/bin/env python3
"""
Game State Serialization System for LAN Multiplayer

Handles complete game state serialization, deserialization, and checksum generation
to ensure perfect synchronization between networked players.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from boneglaive.utils.debug import logger
from boneglaive.utils.constants import UnitType
from boneglaive.game.map import TerrainType


class GameStateSerializer:
    """
    Comprehensive game state serialization system.
    Handles conversion between game objects and network-transmittable data.
    """
    
    def __init__(self):
        self.serialization_version = "1.0.0"
    
    def serialize_game_state(self, game) -> Dict[str, Any]:
        """
        Convert complete game state to serializable dictionary.
        
        Args:
            game: Game engine instance
            
        Returns:
            Dictionary containing complete serialized game state
        """
        try:
            serialized_state = {
                'version': self.serialization_version,
                'timestamp': time.time(),
                
                # Core game state
                'core': self._serialize_core_state(game),
                
                # Map state  
                'map': self._serialize_map_state(game.map),
                
                # All units
                'units': [self._serialize_unit(unit) for unit in game.units],
                
                # Unit count for validation
                'unit_count': len(game.units),
            }
            
            logger.debug(f"Serialized game state: {len(game.units)} units, "
                        f"core state with {len(serialized_state['core'])} properties")
            
            return serialized_state
            
        except Exception as e:
            logger.error(f"Error serializing game state: {str(e)}")
            raise
    
    def deserialize_game_state(self, data: Dict[str, Any], game) -> None:
        """
        Restore complete game state from serialized data.
        
        Args:
            data: Serialized game state dictionary
            game: Game engine instance to restore state to
        """
        try:
            # Validate version compatibility
            version = data.get('version', '0.0.0')
            if version != self.serialization_version:
                logger.warning(f"Version mismatch: local={self.serialization_version}, "
                              f"remote={version}")
            
            # Restore core game state
            self._deserialize_core_state(data['core'], game)
            
            # Restore map state
            self._deserialize_map_state(data['map'], game.map)
            
            # Restore units
            self._deserialize_units(data['units'], game)
            
            # Validate unit count
            expected_count = data.get('unit_count', 0)
            actual_count = len(game.units)
            if actual_count != expected_count:
                logger.error(f"Unit count mismatch after deserialization: "
                           f"expected={expected_count}, actual={actual_count}")
            
            logger.info(f"Deserialized game state: {actual_count} units restored")
            
        except Exception as e:
            logger.error(f"Error deserializing game state: {str(e)}")
            raise
    
    def generate_checksum(self, game) -> str:
        """
        Generate deterministic checksum of complete game state.
        
        Args:
            game: Game engine instance
            
        Returns:
            MD5 checksum string
        """
        try:
            # Serialize state but exclude timestamp for deterministic checksum
            state_data = self.serialize_game_state(game)
            state_data.pop('timestamp', None)  # Remove timestamp
            
            # Create deterministic JSON representation
            json_str = json.dumps(state_data, sort_keys=True, separators=(',', ':'))
            
            # Generate checksum
            checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
            
            logger.debug(f"Generated game state checksum: {checksum}")
            return checksum
            
        except Exception as e:
            logger.error(f"Error generating game state checksum: {str(e)}")
            raise
    
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> List[str]:
        """
        Compare two game states and return list of differences.
        
        Args:
            state1: First game state dictionary
            state2: Second game state dictionary
            
        Returns:
            List of difference descriptions
        """
        differences = []
        
        try:
            # Compare core state
            differences.extend(self._compare_core_states(
                state1.get('core', {}), state2.get('core', {})))
            
            # Compare map state
            differences.extend(self._compare_map_states(
                state1.get('map', {}), state2.get('map', {})))
            
            # Compare unit states
            differences.extend(self._compare_unit_states(
                state1.get('units', []), state2.get('units', [])))
            
        except Exception as e:
            differences.append(f"Error comparing states: {str(e)}")
        
        return differences
    
    def _serialize_core_state(self, game) -> Dict[str, Any]:
        """Serialize complete core game engine state."""
        return {
            # Basic game state
            'current_player': game.current_player,
            'turn': game.turn,
            'winner': game.winner,
            'action_counter': game.action_counter,
            'is_player2_first_turn': game.is_player2_first_turn,
            
            # Game modes and settings
            'local_multiplayer': game.local_multiplayer,
            'test_mode': game.test_mode,
            
            # Map information
            'map_name': game.map_name,
            
            # Setup phase state
            'setup_phase': game.setup_phase,
            'setup_player': game.setup_player,
            'setup_confirmed': game.setup_confirmed.copy(),
            'setup_units_remaining': game.setup_units_remaining.copy(),
            
            # Unit count for validation
            'total_units': len(game.units),
            'units_per_player': {
                1: len([u for u in game.units if u.player == 1]),
                2: len([u for u in game.units if u.player == 2])
            },
            
            # Game events (if event manager exists)
            'has_event_manager': hasattr(game, 'event_manager') and game.event_manager is not None,
        }
    
    def _deserialize_core_state(self, data: Dict[str, Any], game) -> None:
        """Restore complete core game engine state."""
        # Basic game state
        game.current_player = data['current_player']
        game.turn = data['turn']
        game.winner = data['winner']
        game.action_counter = data['action_counter']
        game.is_player2_first_turn = data['is_player2_first_turn']
        
        # Game modes and settings
        game.local_multiplayer = data['local_multiplayer']
        game.test_mode = data['test_mode']
        
        # Map information (verify compatibility)
        expected_map = data.get('map_name', game.map_name)
        if expected_map != game.map_name:
            logger.warning(f"Map mismatch: local={game.map_name}, remote={expected_map}")
        
        # Setup phase state
        game.setup_phase = data['setup_phase']
        game.setup_player = data['setup_player']
        game.setup_confirmed = data['setup_confirmed'].copy()
        game.setup_units_remaining = data['setup_units_remaining'].copy()
        
        # Validate unit counts (will be fully restored in Phase 5.3)
        expected_total = data.get('total_units', 0)
        actual_total = len(game.units)
        if expected_total != actual_total:
            logger.warning(f"Unit count mismatch: expected={expected_total}, actual={actual_total}")
        
        expected_per_player = data.get('units_per_player', {})
        for player in [1, 2]:
            expected = expected_per_player.get(str(player), 0)  # JSON keys are strings
            actual = len([u for u in game.units if u.player == player])
            if expected != actual:
                logger.warning(f"Player {player} unit count mismatch: expected={expected}, actual={actual}")
        
        logger.debug(f"Restored core state: turn={game.turn}, player={game.current_player}, "
                    f"setup={game.setup_phase}, units={len(game.units)}")
    
    def _serialize_map_state(self, game_map) -> Dict[str, Any]:
        """Serialize comprehensive map state including terrain and cosmic values."""
        return {
            'name': game_map.name,
            'height': game_map.height,
            'width': game_map.width,
            
            # Serialize all terrain
            'terrain': {f"{y},{x}": terrain.value 
                       for (y, x), terrain in game_map.terrain.items()},
            
            # Serialize cosmic values for furniture
            'cosmic_values': {f"{y},{x}": value 
                             for (y, x), value in game_map.cosmic_values.items()},
            
            # Map metadata
            'total_terrain_tiles': len(game_map.terrain),
            'cosmic_furniture_count': len(game_map.cosmic_values),
            'terrain_types_present': list(set(terrain.value for terrain in game_map.terrain.values())),
        }
    
    def _deserialize_map_state(self, data: Dict[str, Any], game_map) -> None:
        """Restore comprehensive map terrain and cosmic values."""
        # Validate map compatibility
        if data.get('name') != game_map.name:
            logger.warning(f"Map name mismatch: local={game_map.name}, remote={data.get('name')}")
        if data.get('height') != game_map.height or data.get('width') != game_map.width:
            logger.warning(f"Map dimensions mismatch: local=({game_map.height},{game_map.width}), "
                          f"remote=({data.get('height')},{data.get('width')})")
        
        # Restore terrain
        game_map.terrain = {}
        terrain_data = data.get('terrain', {})
        for pos_str, terrain_value in terrain_data.items():
            y, x = map(int, pos_str.split(','))
            game_map.terrain[(y, x)] = TerrainType(terrain_value)
        
        # Restore cosmic values
        game_map.cosmic_values = {}
        cosmic_data = data.get('cosmic_values', {})
        for pos_str, value in cosmic_data.items():
            y, x = map(int, pos_str.split(','))
            game_map.cosmic_values[(y, x)] = value
        
        # Validate restoration
        expected_terrain_count = data.get('total_terrain_tiles', 0)
        actual_terrain_count = len(game_map.terrain)
        if expected_terrain_count != actual_terrain_count:
            logger.warning(f"Terrain tile count mismatch: expected={expected_terrain_count}, "
                          f"actual={actual_terrain_count}")
        
        expected_cosmic_count = data.get('cosmic_furniture_count', 0)
        actual_cosmic_count = len(game_map.cosmic_values)
        if expected_cosmic_count != actual_cosmic_count:
            logger.warning(f"Cosmic furniture count mismatch: expected={expected_cosmic_count}, "
                          f"actual={actual_cosmic_count}")
        
        logger.debug(f"Restored map state: {actual_terrain_count} terrain tiles, "
                    f"{actual_cosmic_count} cosmic furniture pieces")
    
    def _serialize_unit(self, unit) -> Dict[str, Any]:
        """
        Serialize a single unit's complete state with future-proof extensibility.
        Phase 5.3: Comprehensive unit serialization.
        """
        serialized_unit = {
            # === BASIC PROPERTIES ===
            'type': unit.type.name,
            'player': unit.player,
            'y': unit._y,
            'x': unit._x,
            'greek_id': unit.greek_id,
            
            # === CORE STATS ===
            'max_hp': unit.max_hp,
            'hp': unit._hp,
            'attack': unit.attack,
            'defense': unit.defense,
            'move_range': unit.move_range,
            'attack_range': unit.attack_range,
            
            # === STAT BONUSES ===
            'hp_bonus': unit.hp_bonus,
            'attack_bonus': unit.attack_bonus,
            'defense_bonus': unit.defense_bonus,
            'move_range_bonus': unit.move_range_bonus,
            'attack_range_bonus': unit.attack_range_bonus,
            
            # === ACTION STATE ===
            'action_timestamp': unit.action_timestamp,
            'move_target': unit.move_target,
            'attack_target': unit.attack_target,
            'skill_target': unit.skill_target,
            'selected_skill': self._serialize_skill_reference(unit.selected_skill),
            
            # === EXPERIENCE & LEVELING ===
            'level': unit.level,
            'xp': unit.xp,
            
            # === SKILLS ===
            'passive_skill': self._serialize_skill(unit.passive_skill),
            'active_skills': [self._serialize_skill(skill) for skill in unit.active_skills],
            
            # === STATUS EFFECTS (Future-proof system) ===
            'status_effects': self._serialize_status_effects(unit),
            
            # === VISUAL INDICATORS (Future-proof system) ===
            'visual_indicators': self._serialize_visual_indicators(unit),
            
            # === UNIT REFERENCES (Object relationships) ===
            'unit_references': self._serialize_unit_references(unit),
            
            # === EXTENSIBLE PROPERTIES (Future additions) ===
            'extended_properties': self._serialize_extended_properties(unit),
        }
        
        return serialized_unit
    
    def _serialize_skill(self, skill) -> Optional[Dict[str, Any]]:
        """Serialize a skill object with its state."""
        if skill is None:
            return None
        
        return {
            'class_name': skill.__class__.__name__,
            'name': skill.name,
            'key': skill.key,
            'description': skill.description,
            'skill_type': skill.skill_type.name if hasattr(skill.skill_type, 'name') else str(skill.skill_type),
            'target_type': skill.target_type.name if hasattr(skill.target_type, 'name') else str(skill.target_type),
            'cooldown': skill.cooldown,
            'current_cooldown': skill.current_cooldown,
            'range': skill.range,
            'area': skill.area,
            # Include skill ID for reference matching
            'skill_id': getattr(skill, 'id', f"{skill.name}-{id(skill)}")
        }
    
    def _serialize_skill_reference(self, skill) -> Optional[str]:
        """Serialize a skill reference (for selected_skill)."""
        if skill is None:
            return None
        return getattr(skill, 'id', f"{skill.name}-{id(skill)}")
    
    def _serialize_status_effects(self, unit) -> List[Dict[str, Any]]:
        """
        Serialize all status effects using a future-proof generic system.
        Automatically detects all status effect properties.
        """
        status_effects = []
        
        # Define known status effect patterns
        status_patterns = {
            # Boolean flags with optional durations
            'was_pried': {'type': 'boolean'},
            'took_action': {'type': 'boolean'},
            'took_no_actions': {'type': 'boolean'},
            'jawline_affected': {'type': 'boolean', 'duration_field': 'jawline_duration'},
            'estranged': {'type': 'boolean'},
            'mired': {'type': 'boolean', 'duration_field': 'mired_duration'},
            'is_echo': {'type': 'boolean', 'duration_field': 'echo_duration'},
            'charging_status': {'type': 'boolean'},
            'is_invulnerable': {'type': 'boolean'},
            'diverge_return_position': {'type': 'boolean'},
            'neural_shunt_affected': {'type': 'boolean', 'duration_field': 'neural_shunt_duration'},
            'carrier_rave_active': {'type': 'boolean', 'duration_field': 'carrier_rave_duration'},
            'carrier_rave_strikes_ready': {'type': 'boolean'},
            'can_use_anchor': {'type': 'boolean'},
            
            # Duration-only effects
            'trap_duration': {'type': 'duration', 'base_name': 'trapped'},
            'shrapnel_duration': {'type': 'duration', 'base_name': 'shrapnel'},
            'vapor_duration': {'type': 'duration', 'base_name': 'vapor'},
            
            # Complex status effects
            'radiation_stacks': {'type': 'list', 'base_name': 'radiation'},
            'vapor_type': {'type': 'string', 'base_name': 'vapor_type'},
            'vapor_symbol': {'type': 'string', 'base_name': 'vapor_symbol'},
            'gaussian_charge_direction': {'type': 'value', 'base_name': 'gaussian_charge'},
        }
        
        # Process each status effect
        for field_name, config in status_patterns.items():
            if hasattr(unit, field_name):
                value = getattr(unit, field_name)
                
                # Skip inactive status effects
                if config['type'] == 'boolean' and not value:
                    continue
                if config['type'] == 'duration' and value <= 0:
                    continue
                if config['type'] in ['string', 'value'] and value is None:
                    continue
                if config['type'] == 'list' and not value:
                    continue
                
                # Create status effect entry
                base_name = config.get('base_name', field_name)
                # Clean up field names for better effect names
                if field_name.endswith('_affected'):
                    base_name = field_name.replace('_affected', '')
                
                effect = {
                    'name': base_name,
                    'type': config['type'],
                    'value': value
                }
                
                # Add duration if applicable
                if 'duration_field' in config:
                    duration_field = config['duration_field']
                    if hasattr(unit, duration_field):
                        effect['duration'] = getattr(unit, duration_field)
                
                status_effects.append(effect)
        
        return status_effects
    
    def _serialize_visual_indicators(self, unit) -> Dict[str, Any]:
        """
        Serialize all visual indicators using a generic system.
        Future-proof for new indicator types.
        """
        indicators = {}
        
        # List of known visual indicator fields
        indicator_fields = [
            'vault_target_indicator', 'site_inspection_indicator', 'teleport_target_indicator',
            'expedite_path_indicator', 'jawline_indicator', 'broaching_gas_indicator',
            'saft_e_gas_indicator', 'market_futures_indicator', 'divine_depreciation_indicator',
            'auction_curse_enemy_indicator', 'auction_curse_ally_indicator',
            'gaussian_dusk_indicator', 'big_arc_indicator', 'fragcrest_indicator'
        ]
        
        for field_name in indicator_fields:
            if hasattr(unit, field_name):
                value = getattr(unit, field_name)
                if value is not None:
                    # Remove '_indicator' suffix for cleaner names
                    indicator_name = field_name.replace('_indicator', '')
                    indicators[indicator_name] = value
        
        return indicators
    
    def _serialize_unit_references(self, unit) -> Dict[str, Optional[str]]:
        """
        Serialize unit object references as unit IDs for reconstruction.
        Handles all unit-to-unit relationships.
        """
        references = {}
        
        # Known unit reference fields
        reference_fields = [
            'trapped_by', 'original_unit', 'vapor_creator', 
            'vapor_skill', 'diverged_user'
        ]
        
        for field_name in reference_fields:
            if hasattr(unit, field_name):
                referenced_unit = getattr(unit, field_name)
                if referenced_unit is not None:
                    # Handle different reference types
                    if hasattr(referenced_unit, 'player') and hasattr(referenced_unit, 'greek_id'):
                        # It's a unit reference
                        references[field_name] = f"{referenced_unit.player}_{referenced_unit.greek_id}"
                    elif hasattr(referenced_unit, 'name'):
                        # It's a skill reference
                        references[field_name] = f"skill_{referenced_unit.name}_{id(referenced_unit)}"
                    else:
                        # Generic object reference
                        references[field_name] = str(referenced_unit)
                else:
                    references[field_name] = None
        
        return references
    
    def _serialize_extended_properties(self, unit) -> Dict[str, Any]:
        """
        Serialize any additional properties not covered by the standard system.
        Future-proof extension point for new unit mechanics.
        """
        extended = {}
        
        # Game reference (store if needed for special mechanics)
        if hasattr(unit, '_game') and unit._game is not None:
            extended['has_game_reference'] = True
        
        # First turn movement bonus (special case)
        if hasattr(unit, 'first_turn_move_bonus'):
            extended['first_turn_move_bonus'] = unit.first_turn_move_bonus
        
        # Any other future properties can be added here
        # This provides an extension point without breaking compatibility
        
        return extended
    
    def _deserialize_units(self, units_data: List[Dict[str, Any]], game) -> None:
        """
        Restore all units from serialized data.
        Phase 5.3: Complete unit deserialization with future-proof extensibility.
        """
        from boneglaive.game.units import Unit
        from boneglaive.utils.constants import UnitType
        
        try:
            # Clear existing units
            game.units = []
            
            # Restore each unit
            for unit_data in units_data:
                # Create basic unit
                unit_type = UnitType[unit_data['type']]
                player = unit_data['player']
                y = unit_data['y']
                x = unit_data['x']
                
                unit = Unit(unit_type, player, y, x)
                
                # Restore basic properties
                unit.greek_id = unit_data.get('greek_id')
                
                # Restore core stats
                unit.max_hp = unit_data['max_hp']
                unit._hp = unit_data['hp']
                unit.attack = unit_data['attack']
                unit.defense = unit_data['defense']
                unit.move_range = unit_data['move_range']
                unit.attack_range = unit_data['attack_range']
                
                # Restore stat bonuses
                unit.hp_bonus = unit_data.get('hp_bonus', 0)
                unit.attack_bonus = unit_data.get('attack_bonus', 0)
                unit.defense_bonus = unit_data.get('defense_bonus', 0)
                unit.move_range_bonus = unit_data.get('move_range_bonus', 0)
                unit.attack_range_bonus = unit_data.get('attack_range_bonus', 0)
                
                # Restore action state
                unit.action_timestamp = unit_data.get('action_timestamp', 0)
                unit.move_target = unit_data.get('move_target')
                unit.attack_target = unit_data.get('attack_target')
                unit.skill_target = unit_data.get('skill_target')
                
                # Restore experience & leveling
                unit.level = unit_data.get('level', 1)
                unit.xp = unit_data.get('xp', 0)
                
                # Restore skills (will be handled after all units are created)
                # Store skill data for later reconstruction
                unit._serialized_skills = {
                    'passive_skill': unit_data.get('passive_skill'),
                    'active_skills': unit_data.get('active_skills', []),
                    'selected_skill': unit_data.get('selected_skill')
                }
                
                # Store complex data for later reconstruction (after all units exist)
                unit._serialized_status_effects = unit_data.get('status_effects', [])
                unit._serialized_visual_indicators = unit_data.get('visual_indicators', {})
                unit._serialized_unit_references = unit_data.get('unit_references', {})
                unit._serialized_extended_properties = unit_data.get('extended_properties', {})
                
                game.units.append(unit)
            
            logger.info(f"Created {len(game.units)} units from serialized data")
            
            # Second pass: Restore complex relationships and references
            self._restore_unit_relationships(game)
            
            # Third pass: Initialize skills and finalize unit state
            self._finalize_unit_restoration(game)
            
        except Exception as e:
            logger.error(f"Error deserializing units: {str(e)}")
            # Don't raise exception - let the game continue with existing units
            # raise
    
    def _restore_unit_relationships(self, game) -> None:
        """
        Restore unit-to-unit relationships and status effects.
        Must be called after all units are created.
        """
        try:
            for unit in game.units:
                if not hasattr(unit, '_serialized_status_effects'):
                    continue
                
                # Restore status effects
                self._restore_status_effects(unit, unit._serialized_status_effects)
                
                # Restore visual indicators
                self._restore_visual_indicators(unit, unit._serialized_visual_indicators)
                
                # Restore unit references
                self._restore_unit_references(unit, unit._serialized_unit_references, game)
                
                # Restore extended properties
                self._restore_extended_properties(unit, unit._serialized_extended_properties)
            
            logger.debug("Restored unit relationships and status effects")
            
        except Exception as e:
            logger.error(f"Error restoring unit relationships: {str(e)}")
    
    def _finalize_unit_restoration(self, game) -> None:
        """
        Finalize unit restoration by initializing skills and cleaning up temp data.
        """
        try:
            for unit in game.units:
                # Initialize skills if not already done
                if not hasattr(unit, 'passive_skill') or unit.passive_skill is None:
                    unit.initialize_skills()
                
                # Restore skill cooldowns if available
                if hasattr(unit, '_serialized_skills'):
                    self._restore_skill_cooldowns(unit, unit._serialized_skills)
                
                # Clean up temporary serialization data
                for attr in ['_serialized_skills', '_serialized_status_effects', 
                           '_serialized_visual_indicators', '_serialized_unit_references',
                           '_serialized_extended_properties']:
                    if hasattr(unit, attr):
                        delattr(unit, attr)
            
            logger.debug("Finalized unit restoration")
            
        except Exception as e:
            logger.error(f"Error finalizing unit restoration: {str(e)}")
    
    def _restore_status_effects(self, unit, status_effects_data: List[Dict[str, Any]]) -> None:
        """Restore status effects from serialized data."""
        for effect in status_effects_data:
            effect_name = effect['name']
            effect_type = effect['type']
            value = effect['value']
            duration = effect.get('duration', 0)
            
            # Map effect names back to unit properties
            if effect_type == 'boolean':
                # Find the corresponding boolean field
                possible_fields = [f"{effect_name}_affected", effect_name, f"is_{effect_name}"]
                for field_name in possible_fields:
                    if hasattr(unit, field_name):
                        setattr(unit, field_name, value)
                        break
                
                # Set duration if applicable
                if duration > 0:
                    duration_field = f"{effect_name}_duration"
                    if hasattr(unit, duration_field):
                        setattr(unit, duration_field, duration)
                        
            elif effect_type == 'duration':
                # Direct duration field
                duration_field = f"{effect_name}_duration"
                if hasattr(unit, duration_field):
                    setattr(unit, duration_field, value)
                    
            elif effect_type == 'list':
                # List-based effects like radiation_stacks
                if effect_name == 'radiation' and hasattr(unit, 'radiation_stacks'):
                    unit.radiation_stacks = value
                    
            elif effect_type in ['string', 'value']:
                # String or value fields
                if hasattr(unit, effect_name):
                    setattr(unit, effect_name, value)
    
    def _restore_visual_indicators(self, unit, indicators_data: Dict[str, Any]) -> None:
        """Restore visual indicators from serialized data."""
        for indicator_name, value in indicators_data.items():
            # Reconstruct full field name
            field_name = f"{indicator_name}_indicator"
            if hasattr(unit, field_name):
                setattr(unit, field_name, value)
    
    def _restore_unit_references(self, unit, references_data: Dict[str, Optional[str]], game) -> None:
        """Restore unit object references from unit IDs."""
        for field_name, reference_id in references_data.items():
            if reference_id is None:
                if hasattr(unit, field_name):
                    setattr(unit, field_name, None)
                continue
            
            # Find referenced unit
            if reference_id.startswith('skill_'):
                # Skip skill references for now - complex to restore
                continue
            else:
                # Unit reference
                referenced_unit = self._find_unit_by_id(reference_id, game)
                if referenced_unit and hasattr(unit, field_name):
                    setattr(unit, field_name, referenced_unit)
    
    def _restore_extended_properties(self, unit, extended_data: Dict[str, Any]) -> None:
        """Restore extended properties."""
        for prop_name, value in extended_data.items():
            if prop_name == 'has_game_reference':
                # Set game reference if needed
                continue  # Skip for now
            elif hasattr(unit, prop_name):
                setattr(unit, prop_name, value)
    
    def _restore_skill_cooldowns(self, unit, skills_data: Dict[str, Any]) -> None:
        """Restore skill cooldown states."""
        # This is complex - for now, just ensure skills are initialized
        # Full skill state restoration can be added later if needed
        pass
    
    def _find_unit_by_id(self, unit_id: str, game) -> Optional:
        """Find a unit by its serialized ID (player_greekid)."""
        try:
            parts = unit_id.split('_', 1)
            if len(parts) != 2:
                return None
                
            player = int(parts[0])
            greek_id = parts[1]
            
            for unit in game.units:
                if unit.player == player and unit.greek_id == greek_id:
                    return unit
                    
            return None
        except (ValueError, AttributeError):
            return None
    
    def _compare_core_states(self, state1: Dict, state2: Dict) -> List[str]:
        """Compare core game states and return differences."""
        differences = []
        
        # Compare all core state properties
        core_properties = [
            'current_player', 'turn', 'winner', 'action_counter', 
            'is_player2_first_turn', 'local_multiplayer', 'test_mode',
            'map_name', 'setup_phase', 'setup_player', 'total_units',
            'has_event_manager'
        ]
        
        for key in core_properties:
            if state1.get(key) != state2.get(key):
                differences.append(f"Core.{key}: {state1.get(key)} != {state2.get(key)}")
        
        # Compare setup dictionaries
        setup_confirmed1 = state1.get('setup_confirmed', {})
        setup_confirmed2 = state2.get('setup_confirmed', {})
        if setup_confirmed1 != setup_confirmed2:
            differences.append(f"Core.setup_confirmed: {setup_confirmed1} != {setup_confirmed2}")
            
        setup_remaining1 = state1.get('setup_units_remaining', {})
        setup_remaining2 = state2.get('setup_units_remaining', {})
        if setup_remaining1 != setup_remaining2:
            differences.append(f"Core.setup_units_remaining: {setup_remaining1} != {setup_remaining2}")
        
        # Compare units per player
        units_per_player1 = state1.get('units_per_player', {})
        units_per_player2 = state2.get('units_per_player', {})
        if units_per_player1 != units_per_player2:
            differences.append(f"Core.units_per_player: {units_per_player1} != {units_per_player2}")
        
        return differences
    
    def _compare_map_states(self, state1: Dict, state2: Dict) -> List[str]:
        """Compare map states and return differences."""
        differences = []
        
        # Compare terrain
        terrain1 = state1.get('terrain', {})
        terrain2 = state2.get('terrain', {})
        
        all_positions = set(terrain1.keys()) | set(terrain2.keys())
        for pos in all_positions:
            if terrain1.get(pos) != terrain2.get(pos):
                differences.append(f"Map.terrain[{pos}]: {terrain1.get(pos)} != {terrain2.get(pos)}")
        
        # Compare cosmic values
        cosmic1 = state1.get('cosmic_values', {})
        cosmic2 = state2.get('cosmic_values', {})
        
        all_cosmic_pos = set(cosmic1.keys()) | set(cosmic2.keys())
        for pos in all_cosmic_pos:
            if cosmic1.get(pos) != cosmic2.get(pos):
                differences.append(f"Map.cosmic_values[{pos}]: {cosmic1.get(pos)} != {cosmic2.get(pos)}")
        
        return differences
    
    def _compare_unit_states(self, units1: List[Dict], units2: List[Dict]) -> List[str]:
        """Compare unit states and return differences."""
        differences = []
        
        if len(units1) != len(units2):
            differences.append(f"Unit count: {len(units1)} != {len(units2)}")
            return differences
        
        # Compare each unit (assumes units are in same order)
        # Exclude greek_id from comparison since it's not in serialized data yet
        for i, (unit1, unit2) in enumerate(zip(units1, units2)):
            for key in ['type', 'player', 'y', 'x', 'hp', 'max_hp']:
                if unit1.get(key) != unit2.get(key):
                    differences.append(f"Unit[{i}].{key}: {unit1.get(key)} != {unit2.get(key)}")
        
        return differences


# Create a global serializer instance
game_state_serializer = GameStateSerializer()