#!/usr/bin/env python3
"""
Test script to export existing maps to JSON and verify JSON loading works.
"""
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, '/home/jms/Projects/boneglaive2')

from boneglaive.game.map import MapFactory, StainedStonesMap, NewLimeFoyerMap, EdgecaseMap

def export_map_to_json(map_instance, filename):
    """Export a map instance to JSON file."""
    filepath = f"maps/{filename}"
    print(f"Exporting {map_instance.name} to {filepath}")
    map_instance.to_json(filepath)
    print(f"✅ Exported successfully")

def test_json_loading(filename):
    """Test loading a JSON map."""
    print(f"\n🧪 Testing JSON loading for {filename}")
    try:
        map_name = filename.replace('.json', '')
        loaded_map = MapFactory.create_map(map_name)
        print(f"✅ Loaded '{loaded_map.name}' successfully")
        
        # Basic validation
        print(f"   Size: {loaded_map.width}x{loaded_map.height}")
        
        # Count terrain types
        terrain_count = {}
        for terrain_type in loaded_map.terrain.values():
            terrain_count[terrain_type.name] = terrain_count.get(terrain_type.name, 0) + 1
        
        print(f"   Terrain types: {len(terrain_count)}")
        print(f"   Cosmic values: {len(loaded_map.cosmic_values)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load {filename}: {e}")
        return False

def main():
    print("🗺️  Boneglaive Map Export/Import Test")
    print("=" * 50)
    
    # Test 1: Export existing maps to JSON
    print("\n📤 Phase 1: Exporting existing maps to JSON")
    
    maps_to_export = [
        (StainedStonesMap(), "stained_stones.json"),
        (NewLimeFoyerMap(), "lime_foyer_arena.json"),
        (EdgecaseMap(), "edgecase.json")
    ]
    
    for map_instance, filename in maps_to_export:
        try:
            export_map_to_json(map_instance, filename)
        except Exception as e:
            print(f"❌ Failed to export {filename}: {e}")
    
    # Test 2: Load maps from JSON
    print("\n📥 Phase 2: Testing JSON map loading")
    
    json_files = ["stained_stones.json", "lime_foyer_arena.json", "edgecase.json"]
    success_count = 0
    
    for json_file in json_files:
        if test_json_loading(json_file):
            success_count += 1
    
    # Test 3: List available maps
    print("\n📋 Phase 3: Listing all available maps")
    available_maps = MapFactory.list_available_maps()
    print(f"Available maps: {available_maps}")
    
    # Summary
    print(f"\n📊 Results Summary")
    print(f"   Exported: {len(maps_to_export)} maps")
    print(f"   Loaded successfully: {success_count}/{len(json_files)} maps")
    print(f"   Total available maps: {len(available_maps)}")
    
    if success_count == len(json_files):
        print("🎉 All tests passed! JSON map system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())