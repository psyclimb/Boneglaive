#!/usr/bin/env python3
"""
Test script to verify maps can be loaded and played in-game.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/home/jms/Projects/boneglaive2')

from boneglaive.game.engine import Game
from boneglaive.utils.config import ConfigManager

def test_map_ingame(map_name):
    """Test loading a map in the actual game engine."""
    print(f"🎮 Testing map '{map_name}' in game engine...")
    
    try:
        # Create a game with the specific map
        game = Game(skip_setup=True, map_name=map_name)
        
        print(f"✅ Game created successfully")
        print(f"   Map name: {game.map.name}")
        print(f"   Map size: {game.map.width}x{game.map.height}")
        print(f"   Current player: {game.current_player}")
        print(f"   Units placed: {len(game.units)}")
        print(f"   Setup phase: {game.setup_phase}")
        
        # Check if map has any special terrain
        terrain_count = {}
        for terrain_type in game.map.terrain.values():
            terrain_count[terrain_type.name] = terrain_count.get(terrain_type.name, 0) + 1
        
        print(f"   Terrain types: {len(terrain_count)} different types")
        for terrain, count in terrain_count.items():
            if terrain != 'EMPTY':
                print(f"     - {terrain}: {count} tiles")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load map '{map_name}': {e}")
        return False

def test_menu_map_list():
    """Test the map selection menu functionality."""
    print(f"📋 Testing menu map list functionality...")
    
    try:
        from boneglaive.game.map import MapFactory
        available_maps = MapFactory.list_available_maps()
        
        print(f"✅ MapFactory.list_available_maps() works")
        print(f"   Available maps: {available_maps}")
        
        # Test how the menu would display these
        for map_name in available_maps:
            display_name = map_name.replace('_', ' ').title()
            print(f"   - {map_name} → '{display_name}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test menu map list: {e}")
        return False

def test_config_integration():
    """Test config system integration."""
    print(f"⚙️  Testing config integration...")
    
    try:
        config = ConfigManager()
        
        # Test setting a map
        config.set('selected_map', 'test_arena')
        selected_map = config.get('selected_map')
        
        print(f"✅ Config integration works")
        print(f"   Set selected_map to: test_arena")
        print(f"   Retrieved selected_map: {selected_map}")
        
        # Test with game creation
        game = Game(skip_setup=True, map_name=selected_map)
        print(f"   Game created with map: {game.map.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test config integration: {e}")
        return False

def main():
    print("🗺️  Boneglaive In-Game Map Loading Test")
    print("=" * 50)
    
    # Test 1: Menu map list
    print("\n📋 Phase 1: Menu System")
    menu_success = test_menu_map_list()
    
    # Test 2: Config integration
    print("\n⚙️  Phase 2: Config System")
    config_success = test_config_integration()
    
    # Test 3: Load different maps in game
    print("\n🎮 Phase 3: In-Game Map Loading")
    test_maps = ['test_arena', 'stained_stones', 'lime_foyer_arena', 'edgecase']
    game_success = 0
    
    for map_name in test_maps:
        if test_map_ingame(map_name):
            game_success += 1
        print()  # Add spacing between tests
    
    # Summary
    print("📊 Test Results Summary")
    print(f"   Menu system: {'✅ PASS' if menu_success else '❌ FAIL'}")
    print(f"   Config integration: {'✅ PASS' if config_success else '❌ FAIL'}")
    print(f"   In-game loading: {game_success}/{len(test_maps)} maps loaded successfully")
    
    if menu_success and config_success and game_success == len(test_maps):
        print("🎉 All tests passed! Maps can be selected and played in-game.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())