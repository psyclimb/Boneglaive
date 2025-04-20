#!/usr/bin/env python3
"""
Asset manager for handling game assets (sprites, sounds, etc.).
Currently just maps characters to game entities for text mode,
but can be extended to handle image assets for graphical mode.
"""

from enum import Enum
from typing import Dict, Optional

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
        # Unit symbols - using Unicode symbols for better visuals
        self.unit_tiles = {
            UnitType.GLAIVEMAN: '♞',  # Chess knight symbol for Glaiveman
            UnitType.ARCHER: '♜',     # Chess rook symbol for Archer
            UnitType.MAGE: '♝'        # Chess bishop symbol for Mage
        }
        
        # Terrain symbols - more distinct symbols for terrain types
        self.terrain_tiles = {
            'empty': '·',        # Middle dot for cleaner empty space
            'wall': '█',         # Solid block for walls
            'water': '≈',        # Double tilde for water
            'forest': '♠',       # Spade for forest
            'limestone': '▒',    # Medium shade block for limestone powder
            'dust': '░',         # Light shade block for dust (more visible)
            'pillar': '◯',       # Large circle for pillars
            'furniture': '■'     # Solid square for furniture
        }
        
        # UI symbols - more distinct and professional
        self.ui_tiles = {
            'cursor': '██',      # Solid blocks for cursor (more visible)
            'selected': '◆◆',    # Diamonds for selected unit
            'health': '♥',       # Heart for health
            'attack': '⚔',       # Crossed swords for attack
            'move': '→',         # Arrow for movement
            'target': '◎'        # Target symbol
        }
        
        # Effect symbols - more distinct for better visual feedback
        self.effect_tiles = {
            'glaiveman_attack': '⚔',  # Crossed swords for melee
            'archer_attack': '➶',     # Arrow for ranged
            'mage_attack': '✦'        # Star for magic
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
    
    def reload_assets(self) -> None:
        """Reload assets, e.g., after changing display mode."""
        self._initialize_assets()