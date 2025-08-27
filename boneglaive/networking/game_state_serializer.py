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
        Serialize a single unit's complete state.
        This is a placeholder - will be implemented in Phase 5.3.
        """
        # Basic serialization for now - will be expanded significantly
        # For deterministic checksums, exclude greek_id which may be random
        return {
            'type': unit.type.name,
            'player': unit.player,
            'y': unit._y,
            'x': unit._x,
            'hp': unit._hp,
            'max_hp': unit.max_hp,
            # NOTE: Excluding greek_id for now since it may be non-deterministic
            # TODO: Add all other unit properties in Phase 5.3
        }
    
    def _deserialize_units(self, units_data: List[Dict[str, Any]], game) -> None:
        """
        Restore all units from serialized data.
        This is a placeholder - will be implemented in Phase 5.3.
        """
        # For now, just log that we would restore units
        logger.info(f"Would restore {len(units_data)} units (Phase 5.3 implementation)")
        # TODO: Complete unit deserialization in Phase 5.3
    
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