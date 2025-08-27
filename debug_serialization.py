#!/usr/bin/env python3
"""
Debug script to isolate serialization/deserialization issues.
"""

import sys
sys.path.insert(0, '/home/jms/Projects/boneglaive2')

from boneglaive.game.engine import Game
from boneglaive.networking.game_state_serializer import game_state_serializer
from boneglaive.utils.constants import UnitType

def test_serialization_isolation():
    """Test serialization/deserialization in isolation."""
    
    print("🔍 DEBUGGING SERIALIZATION/DESERIALIZATION")
    print("=" * 50)
    
    # Create test game
    game1 = Game(skip_setup=True, map_name="lime_foyer")
    
    # Add some test units
    unit1 = game1.add_unit(UnitType.GLAIVEMAN, 1, 5, 5)
    unit2 = game1.add_unit(UnitType.GRAYMAN, 2, 10, 10)
    
    if unit1:
        unit1.hp = 80
    if unit2:
        unit2.hp = 90
    
    print(f"📊 ORIGINAL GAME STATE:")
    print(f"   Units count: {len(game1.units)}")
    print(f"   Unit details:")
    for i, unit in enumerate(game1.units):
        print(f"     {i+1}. {unit.type.name} (Player {unit.player}) HP:{unit.hp}/{unit.max_hp} at ({unit.y},{unit.x})")
    
    # Generate checksum
    checksum1 = game_state_serializer.generate_checksum(game1)
    print(f"   Checksum: {checksum1}")
    print()
    
    # Serialize
    print("🔄 SERIALIZING...")
    serialized_data = game_state_serializer.serialize_game_state(game1)
    
    print(f"📦 SERIALIZED DATA:")
    print(f"   Version: {serialized_data.get('version')}")
    print(f"   Unit count in data: {serialized_data.get('unit_count')}")
    print(f"   Actual units array length: {len(serialized_data.get('units', []))}")
    print(f"   Units in array:")
    for i, unit_data in enumerate(serialized_data.get('units', [])):
        print(f"     {i+1}. {unit_data['type']} (Player {unit_data['player']}) HP:{unit_data['hp']}/{unit_data['max_hp']} at ({unit_data['y']},{unit_data['x']})")
    print()
    
    # Create second game for deserialization
    game2 = Game(skip_setup=True, map_name="lime_foyer") 
    
    # Add different units to game2 first
    different_unit = game2.add_unit(UnitType.INTERFERER, 1, 8, 8)
    if different_unit:
        different_unit.hp = 50
        
    print(f"📊 GAME2 BEFORE DESERIALIZATION:")
    print(f"   Units count: {len(game2.units)}")
    print(f"   Unit details:")
    for i, unit in enumerate(game2.units):
        print(f"     {i+1}. {unit.type.name} (Player {unit.player}) HP:{unit.hp}/{unit.max_hp} at ({unit.y},{unit.x})")
    
    checksum2_before = game_state_serializer.generate_checksum(game2)
    print(f"   Checksum before: {checksum2_before}")
    print()
    
    # Deserialize
    print("🔄 DESERIALIZING...")
    try:
        game_state_serializer.deserialize_game_state(serialized_data, game2)
        print("✅ Deserialization completed")
    except Exception as e:
        print(f"❌ Deserialization error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"📊 GAME2 AFTER DESERIALIZATION:")
    print(f"   Units count: {len(game2.units)}")
    print(f"   Unit details:")
    for i, unit in enumerate(game2.units):
        print(f"     {i+1}. {unit.type.name} (Player {unit.player}) HP:{unit.hp}/{unit.max_hp} at ({unit.y},{unit.x})")
    
    checksum2_after = game_state_serializer.generate_checksum(game2)
    print(f"   Checksum after: {checksum2_after}")
    print()
    
    # Compare checksums
    print("🔍 CHECKSUM COMPARISON:")
    print(f"   Original (game1): {checksum1}")
    print(f"   After deserialize: {checksum2_after}")
    print(f"   Match: {'✅ YES' if checksum1 == checksum2_after else '❌ NO'}")
    
    if checksum1 == checksum2_after:
        print("🎉 SERIALIZATION/DESERIALIZATION WORKING CORRECTLY!")
        return True
    else:
        print("⚠️ SERIALIZATION/DESERIALIZATION HAS ISSUES!")
        
        # Deep comparison
        print("\n🔬 DETAILED COMPARISON:")
        
        if len(game1.units) != len(game2.units):
            print(f"   Unit count mismatch: {len(game1.units)} vs {len(game2.units)}")
        
        for i in range(min(len(game1.units), len(game2.units))):
            u1, u2 = game1.units[i], game2.units[i]
            if u1.type != u2.type or u1.player != u2.player or u1.hp != u2.hp:
                print(f"   Unit {i+1} differs:")
                print(f"     Game1: {u1.type.name} P{u1.player} HP{u1.hp} at ({u1.y},{u1.x})")
                print(f"     Game2: {u2.type.name} P{u2.player} HP{u2.hp} at ({u2.y},{u2.x})")
        
        return False

if __name__ == "__main__":
    test_serialization_isolation()