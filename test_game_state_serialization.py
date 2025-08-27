#!/usr/bin/env python3
"""
Unit tests for Game State Serialization System

Tests the GameStateSerializer class to ensure reliable serialization,
deserialization, and checksum generation for multiplayer synchronization.
"""

import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from boneglaive.networking.game_state_serializer import GameStateSerializer
from boneglaive.game.engine import Game
from boneglaive.game.map import GameMap, TerrainType
from boneglaive.utils.constants import UnitType


class TestGameStateSerializer(unittest.TestCase):
    """Test cases for GameStateSerializer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.serializer = GameStateSerializer()
        self.game = Game(skip_setup=True)  # Create game with default units
    
    def test_serializer_initialization(self):
        """Test serializer creates with correct version."""
        self.assertEqual(self.serializer.serialization_version, "1.0.0")
    
    def test_core_state_serialization_round_trip(self):
        """Test core game state serializes and deserializes correctly."""
        # Modify game state to test values
        self.game.current_player = 2
        self.game.turn = 5
        self.game.action_counter = 10
        self.game.is_player2_first_turn = False
        self.game.setup_phase = True
        self.game.setup_player = 2
        self.game.setup_confirmed = {1: True, 2: False}
        self.game.setup_units_remaining = {1: 1, 2: 2}
        
        # Serialize core state
        core_data = self.serializer._serialize_core_state(self.game)
        
        # Verify serialized data
        self.assertEqual(core_data['current_player'], 2)
        self.assertEqual(core_data['turn'], 5)
        self.assertEqual(core_data['action_counter'], 10)
        self.assertEqual(core_data['is_player2_first_turn'], False)
        self.assertEqual(core_data['setup_phase'], True)
        self.assertEqual(core_data['setup_player'], 2)
        self.assertEqual(core_data['setup_confirmed'], {1: True, 2: False})
        self.assertEqual(core_data['setup_units_remaining'], {1: 1, 2: 2})
        # Check enhanced properties
        self.assertEqual(core_data['map_name'], self.game.map_name)
        self.assertEqual(core_data['local_multiplayer'], self.game.local_multiplayer)
        self.assertEqual(core_data['test_mode'], self.game.test_mode)
        self.assertIn('total_units', core_data)
        self.assertIn('units_per_player', core_data)
        
        # Create new game and deserialize
        new_game = Game(skip_setup=True)
        self.serializer._deserialize_core_state(core_data, new_game)
        
        # Verify deserialized values
        self.assertEqual(new_game.current_player, 2)
        self.assertEqual(new_game.turn, 5)
        self.assertEqual(new_game.action_counter, 10)
        self.assertEqual(new_game.is_player2_first_turn, False)
        self.assertEqual(new_game.setup_phase, True)
        self.assertEqual(new_game.setup_player, 2)
        self.assertEqual(new_game.setup_confirmed, {1: True, 2: False})
        self.assertEqual(new_game.setup_units_remaining, {1: 1, 2: 2})
        # Verify enhanced properties
        self.assertEqual(new_game.local_multiplayer, self.game.local_multiplayer)
        self.assertEqual(new_game.test_mode, self.game.test_mode)
    
    def test_map_state_serialization_round_trip(self):
        """Test map state serializes and deserializes correctly."""
        # Modify map terrain
        game_map = self.game.map
        game_map.set_terrain_at(5, 10, TerrainType.LIMESTONE)
        game_map.set_terrain_at(3, 7, TerrainType.FURNITURE)
        
        # Add cosmic values
        game_map.cosmic_values[(5, 10)] = 42
        game_map.cosmic_values[(3, 7)] = 17
        
        # Serialize map state
        map_data = self.serializer._serialize_map_state(game_map)
        
        # Verify serialized data
        self.assertEqual(map_data['terrain']['5,10'], TerrainType.LIMESTONE.value)
        self.assertEqual(map_data['terrain']['3,7'], TerrainType.FURNITURE.value)
        self.assertEqual(map_data['cosmic_values']['5,10'], 42)
        self.assertEqual(map_data['cosmic_values']['3,7'], 17)
        
        # Create new map and deserialize
        new_map = GameMap()
        self.serializer._deserialize_map_state(map_data, new_map)
        
        # Verify deserialized values
        self.assertEqual(new_map.get_terrain_at(5, 10), TerrainType.LIMESTONE)
        self.assertEqual(new_map.get_terrain_at(3, 7), TerrainType.FURNITURE)
        self.assertEqual(new_map.cosmic_values.get((5, 10)), 42)
        self.assertEqual(new_map.cosmic_values.get((3, 7)), 17)
    
    def test_full_game_state_serialization(self):
        """Test complete game state serialization."""
        # Modify game state
        self.game.turn = 3
        self.game.current_player = 2
        
        # Serialize complete state
        serialized_state = self.serializer.serialize_game_state(self.game)
        
        # Verify structure
        self.assertIn('version', serialized_state)
        self.assertIn('timestamp', serialized_state)
        self.assertIn('core', serialized_state)
        self.assertIn('map', serialized_state)
        self.assertIn('units', serialized_state)
        self.assertIn('unit_count', serialized_state)
        
        # Verify core data
        self.assertEqual(serialized_state['core']['turn'], 3)
        self.assertEqual(serialized_state['core']['current_player'], 2)
        
        # Verify unit count matches
        self.assertEqual(serialized_state['unit_count'], len(self.game.units))
        self.assertEqual(len(serialized_state['units']), len(self.game.units))
    
    def test_checksum_generation(self):
        """Test checksum generation is consistent."""
        # Generate checksum twice
        checksum1 = self.serializer.generate_checksum(self.game)
        checksum2 = self.serializer.generate_checksum(self.game)
        
        # Should be identical
        self.assertEqual(checksum1, checksum2)
        self.assertEqual(len(checksum1), 32)  # MD5 hash length
        
        # Modify game state slightly
        original_turn = self.game.turn
        self.game.turn += 1
        
        # Checksum should be different
        checksum3 = self.serializer.generate_checksum(self.game)
        self.assertNotEqual(checksum1, checksum3)
        
        # Restore original state
        self.game.turn = original_turn
        
        # Checksum should match original again
        checksum4 = self.serializer.generate_checksum(self.game)
        self.assertEqual(checksum1, checksum4)
    
    def test_state_comparison(self):
        """Test state comparison finds differences correctly."""
        # Create two identical states
        state1 = self.serializer.serialize_game_state(self.game)
        state2 = self.serializer.serialize_game_state(self.game)
        
        # Should find no differences
        differences = self.serializer.compare_states(state1, state2)
        self.assertEqual(len(differences), 0)
        
        # Modify one state
        state2['core']['turn'] = 999
        state2['core']['current_player'] = 3
        
        # Should find differences
        differences = self.serializer.compare_states(state1, state2)
        self.assertGreater(len(differences), 0)
        
        # Check specific differences
        diff_text = '\n'.join(differences)
        self.assertIn('Core.turn:', diff_text)
        self.assertIn('Core.current_player:', diff_text)
    
    def test_map_comparison_finds_terrain_differences(self):
        """Test map comparison detects terrain changes."""
        # Create two games with different terrain
        game1 = Game(skip_setup=True)
        game2 = Game(skip_setup=True)
        
        # Modify terrain in one game
        game2.map.set_terrain_at(5, 5, TerrainType.LIMESTONE)
        
        # Serialize both
        state1 = self.serializer.serialize_game_state(game1)
        state2 = self.serializer.serialize_game_state(game2)
        
        # Should find terrain difference
        differences = self.serializer.compare_states(state1, state2)
        terrain_diffs = [d for d in differences if 'Map.terrain' in d]
        self.assertGreater(len(terrain_diffs), 0)
    
    def test_unit_serialization_phase_5_3(self):
        """Test Phase 5.3 comprehensive unit serialization."""
        # Get a unit to test with
        if not self.game.units:
            self.skipTest("No units available for testing")
        
        unit = self.game.units[0]
        
        # Serialize the unit
        serialized_unit = self.serializer._serialize_unit(unit)
        
        # Verify all major sections are present
        expected_sections = [
            'type', 'player', 'y', 'x', 'greek_id',
            'max_hp', 'hp', 'attack', 'defense', 'move_range', 'attack_range',
            'hp_bonus', 'attack_bonus', 'defense_bonus', 'move_range_bonus', 'attack_range_bonus',
            'action_timestamp', 'move_target', 'attack_target', 'skill_target',
            'level', 'xp', 'passive_skill', 'active_skills',
            'status_effects', 'visual_indicators', 'unit_references', 'extended_properties'
        ]
        
        for section in expected_sections:
            self.assertIn(section, serialized_unit, f"Missing section: {section}")
        
        # Verify basic data types
        self.assertIsInstance(serialized_unit['status_effects'], list)
        self.assertIsInstance(serialized_unit['visual_indicators'], dict)
        self.assertIsInstance(serialized_unit['unit_references'], dict)
        self.assertIsInstance(serialized_unit['extended_properties'], dict)
        self.assertIsInstance(serialized_unit['active_skills'], list)
    
    def test_unit_comparison_comprehensive(self):
        """Test comprehensive unit comparison with Phase 5.3 features."""
        state1 = self.serializer.serialize_game_state(self.game)
        state2 = self.serializer.serialize_game_state(self.game)
        
        # Modify unit in state2
        if len(state2['units']) > 0:
            state2['units'][0]['hp'] = 999
            state2['units'][0]['level'] = 5
            
            # Should detect unit differences
            differences = self.serializer.compare_states(state1, state2)
            unit_diffs = [d for d in differences if 'Unit[' in d]
            self.assertGreater(len(unit_diffs), 0)
    
    def test_status_effects_serialization(self):
        """Test status effects serialization system."""
        if not self.game.units:
            self.skipTest("No units available for testing")
        
        unit = self.game.units[0]
        
        # Set some test status effects
        unit.jawline_affected = True
        unit.jawline_duration = 3
        unit.estranged = True
        unit.trap_duration = 2
        
        # Serialize status effects
        status_effects = self.serializer._serialize_status_effects(unit)
        
        # Should capture active effects
        effect_names = [effect['name'] for effect in status_effects]
        self.assertIn('jawline', effect_names)
        self.assertIn('estranged', effect_names)
        self.assertIn('trapped', effect_names)
        
        # Check duration is captured
        jawline_effect = next((e for e in status_effects if e['name'] == 'jawline'), None)
        self.assertIsNotNone(jawline_effect)
        self.assertEqual(jawline_effect['duration'], 3)
    
    def test_visual_indicators_serialization(self):
        """Test visual indicators serialization system."""
        if not self.game.units:
            self.skipTest("No units available for testing")
        
        unit = self.game.units[0]
        
        # Set some test indicators
        unit.vault_target_indicator = (5, 10)
        unit.jawline_indicator = [(3, 4), (3, 5)]
        
        # Serialize indicators
        indicators = self.serializer._serialize_visual_indicators(unit)
        
        # Should capture indicators with cleaned names
        self.assertIn('vault_target', indicators)
        self.assertIn('jawline', indicators)
        self.assertEqual(indicators['vault_target'], (5, 10))
        self.assertEqual(indicators['jawline'], [(3, 4), (3, 5)])
    
    def test_unit_references_serialization(self):
        """Test unit reference serialization system."""
        if len(self.game.units) < 2:
            self.skipTest("Need at least 2 units for reference testing")
        
        unit1 = self.game.units[0]
        unit2 = self.game.units[1]
        
        # Set up a reference
        unit1.trapped_by = unit2
        
        # Serialize references
        references = self.serializer._serialize_unit_references(unit1)
        
        # Should capture the reference as an ID
        self.assertIn('trapped_by', references)
        expected_id = f"{unit2.player}_{unit2.greek_id}"
        self.assertEqual(references['trapped_by'], expected_id)
    
    def test_enhanced_core_state_properties(self):
        """Test Phase 5.2 enhanced core state properties."""
        # Set various game properties
        self.game.test_mode = True
        self.game.local_multiplayer = True
        self.game.map_name = "test_map"
        
        # Serialize state
        core_data = self.serializer._serialize_core_state(self.game)
        
        # Verify enhanced properties are captured
        self.assertEqual(core_data['test_mode'], True)
        self.assertEqual(core_data['local_multiplayer'], True)
        self.assertEqual(core_data['map_name'], "test_map")
        self.assertIn('total_units', core_data)
        self.assertIn('units_per_player', core_data)
        self.assertIn('has_event_manager', core_data)
        
        # Verify unit counts
        expected_total = len(self.game.units)
        self.assertEqual(core_data['total_units'], expected_total)
        
        # Verify units per player count
        units_per_player = core_data['units_per_player']
        p1_count = len([u for u in self.game.units if u.player == 1])
        p2_count = len([u for u in self.game.units if u.player == 2])
        self.assertEqual(units_per_player[1], p1_count)
        self.assertEqual(units_per_player[2], p2_count)
    
    def test_version_handling(self):
        """Test version compatibility checking."""
        # Create state with different version
        state_data = self.serializer.serialize_game_state(self.game)
        state_data['version'] = '2.0.0'  # Different version
        
        # Create new game for deserialization
        new_game = Game(skip_setup=True)
        
        # Should handle version mismatch gracefully (with warning)
        try:
            self.serializer.deserialize_game_state(state_data, new_game)
            # Should not raise exception, just log warning
        except Exception as e:
            self.fail(f"Version mismatch should not raise exception: {e}")
    
    def test_error_handling(self):
        """Test error handling for invalid data."""
        new_game = Game(skip_setup=True)
        
        # Test with invalid data structure
        invalid_data = {'invalid': 'data'}
        
        with self.assertRaises(Exception):
            self.serializer.deserialize_game_state(invalid_data, new_game)
    
    def test_empty_states_comparison(self):
        """Test comparison of empty/minimal states."""
        empty_state1 = {'core': {}, 'map': {}, 'units': []}
        empty_state2 = {'core': {}, 'map': {}, 'units': []}
        
        differences = self.serializer.compare_states(empty_state1, empty_state2)
        # Should handle empty states without crashing
        self.assertIsInstance(differences, list)


class TestGameStateIntegration(unittest.TestCase):
    """Integration tests for game state serialization."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.serializer = GameStateSerializer()
    
    def test_multiple_games_different_checksums(self):
        """Test that different games produce different checksums."""
        # Use the same game instance to ensure deterministic starting state
        game1 = Game(skip_setup=True, map_name="lime_foyer_arena")
        
        # Get baseline checksum
        checksum1 = self.serializer.generate_checksum(game1)
        
        # Modify the game
        game1.turn = 10
        
        # Should now be different
        checksum2 = self.serializer.generate_checksum(game1)
        self.assertNotEqual(checksum1, checksum2)
        
        # Restore original state
        game1.turn = 1
        
        # Should match original again
        checksum3 = self.serializer.generate_checksum(game1)
        self.assertEqual(checksum1, checksum3)
    
    def test_serialization_preserves_game_functionality(self):
        """Test that serialized/deserialized game still functions."""
        # Create and modify original game
        original_game = Game(skip_setup=True)
        original_game.turn = 5
        original_game.current_player = 2
        
        # Serialize and deserialize
        state_data = self.serializer.serialize_game_state(original_game)
        restored_game = Game(skip_setup=True)
        self.serializer.deserialize_game_state(state_data, restored_game)
        
        # Verify core functionality preserved
        self.assertEqual(restored_game.turn, 5)
        self.assertEqual(restored_game.current_player, 2)
        
        # Test that game methods still work
        self.assertIsNotNone(restored_game.map)
        self.assertTrue(hasattr(restored_game, 'units'))


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    # Run tests
    unittest.main(verbosity=2)