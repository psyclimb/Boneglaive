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
            UnitType.MAGE: 'M',
            UnitType.MANDIBLE_FOREMAN: 'F',
            UnitType.GRAYMAN: 'Ψ',
            UnitType.MARROW_CONDENSER: 'C'
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
            'furniture': '#',  # Generic furniture uses hash symbol
            'coat_rack': 'ł',  # Coat rack uses slashed l
            'ottoman': '=',    # Ottoman uses equals sign
            'console': 'ε',    # Console table uses epsilon
            'dec_table': 'Π',  # Decorative table uses Pi symbol
            'marrow_wall': '#'  # Marrow Dike wall uses hash character
        }
        
        # UI symbols
        self.ui_tiles = {
            'cursor': '[]',
            'selected': '**',
            'health': 'HP',
            'vault_target': '◎',  # Circle target for vault landing spot
            'site_inspection': '□',  # Square outline for Site Inspection target
            'teleport_target': 'Δ'  # Greek delta for teleport landing spot
        }
        
        # Effect symbols - enhanced ASCII for attacks
        self.effect_tiles = {
            'glaiveman_attack': '⚔',      # Crossed swords for melee
            'archer_attack': '→',         # Arrow for ranged
            'mage_attack': '*',           # Star for magic
            'mandible_foreman_attack': 'Ξ', # Mandible jaws (melee)
            'grayman_attack': '≈',        # Reality distortion (ranged)
            'marrow_condenser_attack': 'Ø' # Bone symbol for melee
        }
        
        # Add animation sequence tiles for each attack type (using simple ASCII)
        self.animation_sequences = {
            'glaiveman_attack': ['\\', '|', '/', '-', '⚔', '-', '/', '|', '\\'],  # Melee range 1 attack
            'glaiveman_extended_attack': ['/', '―', '\\', '|', '─', '─', '─', '═', '→', '⚔'],  # Extended range 2 attack
            'archer_attack': ['.', '>', '-', '>', '->'],
            'mage_attack': ['.', '*', '*', '*', '*'],
            'mandible_foreman_attack': ['<', '[', '{', 'Ξ', '}', ']', '>'],  # Jaws opening and closing animation
            'grayman_attack': ['·', ':', '≈', '≋', '≈', ':', '·'],  # Reality distortion wave
            'autoclave': ['*', '+', 'x', '#', 'X', '#', 'x', '+', '*'],  # Intense cross pattern for Autoclave
            'pry_range1': ['┘', '┐', '┌', '└', '/'],  # Close-range prying motion - glaive used as lever
            'pry_range2': ['/', '―', '\\', '|', '─', '─', '═', '→', '↗'],  # Extended range prying motion - similar to extended attack
            'pry_launch': ['↑', '↟', '⇑', ' '],  # Unit being launched straight up (single character symbols)
            'pry_impact': ['↓', 'V', '@', '*', '.'],  # Unit falling back down with heavy impact
            'pry_debris': ['@', '#', '*', '+', '.'],  # Large chunks of debris falling straight down
            'vault': ['^', 'Λ', '↑', '↟', '↑'],  # Vault initiation animation - upward movement
            'vault_impact': ['↓', 'v', 'V', '*', '.'],  # Vault landing animation
            'judgement_throw': ['*', '↺', '↻', '⚡', '⚓', '⊕'],  # Sacred glaive animation
            'judgement_critical': ['⚡', '⌁', '⌁', '⚡', '※'],  # Lightning strike critical effect
            'viseroy_trap': ['[]', '><', '}{', 'Ξ', '}{', '><', '[]'],  # Animation for Viseroy trapping
            # MARROW_CONDENSER animations
            'marrow_condenser_attack': ['/', '|', '\\', '-', '8', '$', 'Ø', '#', '*'],  # Swinging and striking with bone chunks
            'ossify': ['#', '%', '@', '*', '+', '=', '&', '$', '#', '/', '\\', '|', '-', '.'],  # ASCII bone hardening animation
            'marrow_dike': ['╎', '╏', '┃', '┆', '┇', '┊', '┋', '#', '#'],  # Marrow wall forming - hash wall animation
            'slough': ['↑', '↗', '→', '↘', '↓'],  # Transfer animation
            'site_inspection': ['□', '■', '□', '■', '□'],  # Animation for Site Inspection
            'discharge_release': ['{⚡}', '<>>', '(  )', '    '],  # Animation for Discharge releasing unit
            'discharge_impact': ['!', '!', '#', 'X', '*', '.'],  # Animation for Discharge impact
            'delta_config': ['Ψ', '░', '▒', '▓', ' ', '▓', '▒', '░', 'Ψ'],  # Teleportation effect
            'teleport_out': ['Ψ', '░', '▒', '▓', ' '],  # Teleport out animation
            'teleport_in': [' ', '▓', '▒', '░', 'Ψ'],  # Teleport in animation
            'estrange': ['≡', '≢', '⋍', '≈', '~', '≈', '⋍', '≢', '≡'],  # Phasing effect
            'grae_exchange': ['|', '/', '_', '*', 'ψ', 'Ψ'],  # Cane tapping and echo creation effect
            'marrow_healing': ['♥', '❤', '♡', '❤', '♥', '✚', '+', '*']  # Blood plasma healing animation
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
            UnitType.MAGE: 'assets/sprites/mage.png',
            UnitType.MANDIBLE_FOREMAN: 'assets/sprites/mandible_foreman.png',
            UnitType.GRAYMAN: 'assets/sprites/grayman.png',
            UnitType.MARROW_CONDENSER: 'assets/sprites/marrow_condenser.png'
        }
        
        self.terrain_tiles = {
            'empty': 'assets/tiles/floor.png',
            'wall': 'assets/tiles/wall.png',
            'water': 'assets/tiles/water.png',
            'forest': 'assets/tiles/forest.png',
            'limestone': 'assets/tiles/limestone.png',
            'dust': 'assets/tiles/dust.png',
            'pillar': 'assets/tiles/pillar.png',
            'furniture': 'assets/tiles/furniture.png',
            'marrow_wall': 'assets/tiles/marrow_wall.png'
        }
        
        self.ui_tiles = {
            'cursor': 'assets/ui/cursor.png',
            'selected': 'assets/ui/selected.png',
            'health': 'assets/ui/health.png',
            'vault_target': 'assets/ui/vault_target.png',
            'site_inspection': 'assets/ui/site_inspection.png',
            'teleport_target': 'assets/ui/teleport_target.png'
        }
        
        self.effect_tiles = {
            'glaiveman_attack': 'assets/effects/glaive.png',
            'archer_attack': 'assets/effects/arrow.png',
            'mage_attack': 'assets/effects/magic.png',
            'mandible_foreman_attack': 'assets/effects/mandibles.png',
            'grayman_attack': 'assets/effects/distortion.png',
            'marrow_condenser_attack': 'assets/effects/bone.png'
        }
        
        # Add animation sequences for graphical mode too
        self.animation_sequences = {
            'glaiveman_attack': ['glaiveman_attack_1.png', 'glaiveman_attack_2.png', 'glaiveman_attack_3.png'],
            'glaiveman_extended_attack': ['glaiveman_extend_1.png', 'glaiveman_extend_2.png', 'glaiveman_extend_3.png', 'glaiveman_extend_4.png', 'glaiveman_extend_5.png'],
            'archer_attack': ['archer_attack_1.png', 'archer_attack_2.png', 'archer_attack_3.png'],
            'mage_attack': ['mage_attack_1.png', 'mage_attack_2.png', 'mage_attack_3.png'],
            'mandible_foreman_attack': ['mandible_attack_1.png', 'mandible_attack_2.png', 'mandible_attack_3.png', 'mandible_attack_4.png'],
            'autoclave': ['autoclave_1.png', 'autoclave_2.png', 'autoclave_3.png', 'autoclave_4.png'],
            'pry_range1': ['pry_range1_1.png', 'pry_range1_2.png', 'pry_range1_3.png'],
            'pry_range2': ['pry_range2_1.png', 'pry_range2_2.png', 'pry_range2_3.png', 'pry_range2_4.png', 'pry_range2_5.png', 'pry_range2_6.png', 'pry_range2_7.png', 'pry_range2_8.png', 'pry_range2_9.png'],
            'pry_launch': ['pry_launch_1.png', 'pry_launch_2.png', 'pry_launch_3.png', 'pry_launch_4.png'],
            'pry_impact': ['pry_impact_1.png', 'pry_impact_2.png', 'pry_impact_3.png'],
            'pry_debris': ['pry_debris_1.png', 'pry_debris_2.png', 'pry_debris_3.png'],
            'vault': ['vault_1.png', 'vault_2.png', 'vault_3.png', 'vault_4.png'],
            'vault_impact': ['vault_impact_1.png', 'vault_impact_2.png', 'vault_impact_3.png'],
            'judgement_throw': ['judgement_throw_1.png', 'judgement_throw_2.png', 'judgement_throw_3.png', 'judgement_throw_4.png'],
            'judgement_critical': ['judgement_critical_1.png', 'judgement_critical_2.png', 'judgement_critical_3.png'],
            'discharge_release': ['discharge_release_1.png', 'discharge_release_2.png', 'discharge_release_3.png'],
            'discharge_impact': ['discharge_impact_1.png', 'discharge_impact_2.png', 'discharge_impact_3.png'],
            'grayman_attack': ['grayman_attack_1.png', 'grayman_attack_2.png', 'grayman_attack_3.png'],
            'delta_config': ['delta_config_1.png', 'delta_config_2.png', 'delta_config_3.png', 'delta_config_4.png'],
            'estrange': ['estrange_1.png', 'estrange_2.png', 'estrange_3.png'],
            'grae_exchange': ['grae_exchange_1.png', 'grae_exchange_2.png', 'grae_exchange_3.png'],
            # MARROW_CONDENSER animations
            'marrow_condenser_attack': ['marrow_attack_1.png', 'marrow_attack_2.png', 'marrow_attack_3.png'],
            'ossify': ['ossify_1.png', 'ossify_2.png', 'ossify_3.png'],
            'marrow_dike': ['marrow_dike_1.png', 'marrow_dike_2.png', 'marrow_dike_3.png'],
            'slough': ['slough_1.png', 'slough_2.png', 'slough_3.png']
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
            UnitType.MAGE: 'mage_attack',
            UnitType.MANDIBLE_FOREMAN: 'mandible_foreman_attack',
            UnitType.GRAYMAN: 'grayman_attack',
            UnitType.MARROW_CONDENSER: 'marrow_condenser_attack'
        }
        effect_type = effect_map.get(unit_type, 'glaiveman_attack')
        return self.get_effect_tile(effect_type)
        
    def get_attack_animation_sequence(self, unit_type: UnitType) -> List[str]:
        """Get the animation sequence for an attack type."""
        effect_map = {
            UnitType.GLAIVEMAN: 'glaiveman_attack',
            UnitType.ARCHER: 'archer_attack',
            UnitType.MAGE: 'mage_attack',
            UnitType.MANDIBLE_FOREMAN: 'mandible_foreman_attack',
            UnitType.GRAYMAN: 'grayman_attack',
            UnitType.MARROW_CONDENSER: 'marrow_condenser_attack'
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