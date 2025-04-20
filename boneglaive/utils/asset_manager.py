#!/usr/bin/env python3
"""
Asset manager for handling game assets (sprites, sounds, etc.).
Currently just maps characters to game entities for text mode,
but can be extended to handle image assets for graphical mode.
"""

from enum import Enum
from typing import Dict, Optional, List

from boneglaive.utils.config import ConfigManager
from boneglaive.utils.constants import UnitType

class AssetManager:
    """
    Manages loading and accessing game assets.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.unit_tiles: Dict[UnitType, str] = {}
        self.terrain_tiles: Dict[str, str] = {}
        self.ui_tiles: Dict[str, str] = {}
        self.effect_tiles: Dict[str, str] = {}
        self._initialize_assets()
    
    def _initialize_assets(self) -> None:
        """Initialize assets based on display mode."""
        # For text mode, assets are just characters
        if self.config_manager.is_text_mode():
            self._initialize_text_assets()
        else:
            # In graphical mode, these would be paths to image files
            self._initialize_graphical_assets()
    
    def _initialize_text_assets(self) -> None:
        """Initialize text-based assets (ASCII/Unicode characters)."""
        # Unit symbols
        self.unit_tiles = {
            UnitType.GLAIVEMAN: 'G',
            UnitType.ARCHER: 'A',
            UnitType.MAGE: 'M'
        }
        
        # Terrain symbols
        self.terrain_tiles = {
            'empty': '.',
            'wall': '#',
            'water': '~',
            'forest': '^',
            'limestone': '▒',  # Limestone powder piles use a medium shade block
            'dust': ',',       # Light limestone dusting use a comma
            'pillar': 'O',     # Pillars use capital O
            'furniture': '■'   # Furniture uses a solid square
        }
        
        # UI symbols
        self.ui_tiles = {
            'cursor': '[]',
            'selected': '**',
            'health': 'HP'
        }
        
        # Effect symbols - enhanced ASCII for attacks
        self.effect_tiles = {
            'glaiveman_attack': '⚔',  # Crossed swords for melee
            'archer_attack': '→',     # Arrow for ranged
            'mage_attack': '*'        # Star for magic
        }
        
        # Add animation sequence tiles for each attack type (using simple ASCII)
        self.animation_sequences = {
            'glaiveman_attack': ['\\', '|', '/', '-', '⚔', '-', '/', '|', '\\'],
            'archer_attack': ['.', '>', '-', '>', '->'],
            'mage_attack': ['.', '*', '*', '*', '*'],
            'autoclave': ['*', '+', 'x', '#', 'X', '#', 'x', '+', '*'],  # Intense cross pattern for Autoclave
            'pry': ['/', '|', '_', '/', '↑', '↗', '→'],  # Lever-like prying motion
            'pry_impact': ['v', 'V', '#', '*', '.']  # Simple ground impact animation for Pry landing
        }
    
    def _initialize_graphical_assets(self) -> None:
        """
        Initialize graphical assets (placeholder).
        In a graphical implementation, this would load actual sprites.
        """
        # These would be asset paths in graphical mode
        self.unit_tiles = {
            UnitType.GLAIVEMAN: 'assets/sprites/glaiveman.png',
            UnitType.ARCHER: 'assets/sprites/archer.png',
            UnitType.MAGE: 'assets/sprites/mage.png'
        }
        
        self.terrain_tiles = {
            'empty': 'assets/tiles/floor.png',
            'wall': 'assets/tiles/wall.png',
            'water': 'assets/tiles/water.png',
            'forest': 'assets/tiles/forest.png',
            'limestone': 'assets/tiles/limestone.png',
            'dust': 'assets/tiles/dust.png',
            'pillar': 'assets/tiles/pillar.png',
            'furniture': 'assets/tiles/furniture.png'
        }
        
        self.ui_tiles = {
            'cursor': 'assets/ui/cursor.png',
            'selected': 'assets/ui/selected.png',
            'health': 'assets/ui/health.png'
        }
        
        self.effect_tiles = {
            'glaiveman_attack': 'assets/effects/glaive.png',
            'archer_attack': 'assets/effects/arrow.png',
            'mage_attack': 'assets/effects/magic.png'
        }
        
        # Add animation sequences for graphical mode too
        self.animation_sequences = {
            'glaiveman_attack': ['glaiveman_attack_1.png', 'glaiveman_attack_2.png', 'glaiveman_attack_3.png'],
            'archer_attack': ['archer_attack_1.png', 'archer_attack_2.png', 'archer_attack_3.png'],
            'mage_attack': ['mage_attack_1.png', 'mage_attack_2.png', 'mage_attack_3.png'],
            'autoclave': ['autoclave_1.png', 'autoclave_2.png', 'autoclave_3.png', 'autoclave_4.png'],
            'pry': ['pry_1.png', 'pry_2.png', 'pry_3.png', 'pry_4.png'],
            'pry_impact': ['pry_impact_1.png', 'pry_impact_2.png', 'pry_impact_3.png']
        }
    
    def get_unit_tile(self, unit_type: UnitType) -> str:
        """Get the tile representation for a unit type."""
        return self.unit_tiles.get(unit_type, '?')
    
    def get_terrain_tile(self, terrain_type: str) -> str:
        """Get the tile representation for a terrain type."""
        return self.terrain_tiles.get(terrain_type, '?')
    
    def get_ui_tile(self, ui_element: str) -> str:
        """Get the tile representation for a UI element."""
        return self.ui_tiles.get(ui_element, '?')
    
    def get_effect_tile(self, effect_type: str) -> str:
        """Get the tile representation for an effect."""
        return self.effect_tiles.get(effect_type, '?')
    
    def get_attack_effect(self, unit_type: UnitType) -> str:
        """Get the attack effect for a unit type."""
        effect_map = {
            UnitType.GLAIVEMAN: 'glaiveman_attack',
            UnitType.ARCHER: 'archer_attack',
            UnitType.MAGE: 'mage_attack'
        }
        effect_type = effect_map.get(unit_type, 'glaiveman_attack')
        return self.get_effect_tile(effect_type)
        
    def get_attack_animation_sequence(self, unit_type: UnitType) -> List[str]:
        """Get the animation sequence for an attack type."""
        effect_map = {
            UnitType.GLAIVEMAN: 'glaiveman_attack',
            UnitType.ARCHER: 'archer_attack',
            UnitType.MAGE: 'mage_attack'
        }
        effect_type = effect_map.get(unit_type, 'glaiveman_attack')
        return self.animation_sequences.get(effect_type, [])
        
    def get_skill_animation_sequence(self, skill_name: str) -> List[str]:
        """Get the animation sequence for a specific skill."""
        # Convert skill name to lowercase for case-insensitive matching
        skill_key = skill_name.lower()
        # Return the animation sequence or an empty list if not found
        return self.animation_sequences.get(skill_key, [])
    
    def reload_assets(self) -> None:
        """Reload assets, e.g., after changing display mode."""
        self._initialize_assets()