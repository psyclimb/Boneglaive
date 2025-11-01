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
            UnitType.MARROW_CONDENSER: 'C',
            UnitType.FOWL_CONTRIVANCE: 'T',
            UnitType.GAS_MACHINIST: 'M',
            UnitType.HEINOUS_VAPOR: 'V',  # Base symbol, will be replaced by vapor_symbol in display code
            UnitType.DELPHIC_APPRAISER: 'A',  # A for Appraiser
            UnitType.DERELICTIONIST: 'D',  # D for DERELICTIONIST
            UnitType.INTERFERER: 'R',  # R for Radioactive interference
            UnitType.POTPOURRIST: 'P'  # P for POTPOURRIST
        }
        
        # Terrain symbols
        self.terrain_tiles = {
            'empty': '.',
            'wall': '#',
            'water': '~',
            'forest': '^',
            'limestone': '#',  # Limestone powder piles use hash symbol
            'dust': ',',       # Light limestone dusting use a comma
            'pillar': 'O',     # Pillars use capital O
            'furniture': '#',  # Generic furniture uses hash symbol
            'coat_rack': 'Y',  # Coat rack uses Y
            'ottoman': '=',    # Ottoman uses equals sign
            'console': '=',    # Console table (flat surface)
            'dec_table': '=',  # Decorative table (flat surface)
            'marrow_wall': '#',  # Marrow Dike wall uses hash character
            'rail': '+',      # Rail track uses cross symbol for intersections
            # Stained Stones map terrain
            'tiffany_lamp': 'i',  # Tiffany lamp (lamp post shape)
            'stained_stone': '#',  # Full block for stained stone formations  
            'easel': 'h',      # Lowercase h resembles easel frame with crossbar
            'sculpture': '*',   # Sculpture (decorative art piece)
            'bench': 'n',      # Lowercase n resembles bench with legs
            'podium': '^',     # Elevated podium platform
            'vase': 'v',       # Lowercase v resembles vase shape
            'canyon_floor': '.',  # Canyon floor sediment
            # Edge Case map terrain - Industrial warehouse converted to home
            'hydraulic_press': 'O',  # Round shape for massive hydraulic press
            'workbench': 'I',  # I-beam shape for industrial workbench
            'couch': 'u',      # Lowercase u resembles couch shape
            'toolbox': '&',    # Ampersand for complex toolbox shape
            'cot': '=',      # Equals sign for flat elevated sleeping surface
            'conveyor': '~',   # Tilde for moving conveyor belt
            'concrete_floor': '.',  # Concrete warehouse floor
            # Seasonal terrain types (autumn)
            'leaf_pit': '*',       # Asterisk for scattered leaves
            'mini_pumpkin': 'o',   # Lowercase o for small round pumpkin
            'potpourri_bowl': 'u', # Lowercase u for bowl shape
            'melange_fume': '~'    # Tilde for aromatic fumes
        }
        
        # UI symbols
        self.ui_tiles = {
            'cursor': '[]',
            'selected': '**',
            'health': 'HP',
            'vault_target': 'X',  # X marker for vault landing spot
            'site_inspection': '#',  # Site Inspection target
            'teleport_target': 'Δ'  # Delta Config landing spot
        }
        
        # Effect symbols - enhanced ASCII for attacks
        self.effect_tiles = {
            'glaiveman_attack': '⚔',      # Crossed swords for melee
            'archer_attack': '→',         # Arrow for ranged
            'mage_attack': '*',           # Star for magic
            'mandible_foreman_attack': '{', # Mandible jaws (melee)
            'grayman_attack': '≈',        # Reality distortion (ranged)
            'marrow_condenser_attack': 'Ø', # Bone symbol for melee
            'fowl_contrivance_attack': '>', # Rail artillery projectile symbol
            'delphic_appraiser_attack': '$', # Currency symbol for evaluation
            'interferer_attack': 'x',  # Plutonium carabiner cross
            'potpourrist_attack': 'I'  # Granite pedestal strike
        }
        
        # Add animation sequence tiles for each attack type (using simple ASCII)
        self.animation_sequences = {
            'glaiveman_attack': ['-', '\\', '|', '/', '\\', '-', '/', '|', '\\', '-'],  # Melee range 1 attack
            'glaiveman_extended_attack': ['-', '=', '>', '>', '|', '|', '*', 'X', 'x'],  # Blade extending progressively further
            'archer_attack': ['.', '-', '=', '>', '*'],  # Arrow flying progressively
            'mage_attack': ['.', '*', '*', '*', '*'],
            'mandible_foreman_attack': ['<', '[', '{', '{', '{', '{'],  # Jaws opening and closing animation
            'grayman_attack': ['.', ':', '~', '~', '~', ':', '.'],  # Reality distortion wave
            'autoclave': ['*', '+', 'x', '#', 'X', '#', 'x', '+', '*'],  # Intense cross pattern for Autoclave
            'pry_range1': ['/', '|', '\\', '_', '-', '^'],  # Close-range prying motion with similar visual language to extended range
            'pry_range2': ['-', '\\', '_', '_', '_', '/'],  # Extended range prying motion - similar to extended attack
            'pry_launch': ['-', '/', '|', 'I', 'i', '^', '.', ' '],  # Unit being pried from horizontal to vertical, then diminishing as it launches upward
            'pry_impact': ['v', 'V', '@', '*', '.'],  # Unit falling back down with heavy impact
            'pry_debris': ['@', '#', '*', '+', '.'],  # Large chunks of debris falling straight down
            'vault': ['^', '^', '^', '^', '^'],  # Vault initiation animation - upward movement
            'vault_impact': ['v', 'v', 'V', '*', '.'],  # Vault landing animation
            'judgement': ['*', '+', 'X', '#', 'O', '#', 'X', '+', '*'],  # Circular spinning Krull glaive animation - ASCII only
            'judgement_critical': ['X', '!', 'Z', '#', 'Z', '#', '*', '!', 'Z', '!', '*', '!'],  # Lightning striking the glaive at moment of critical impact - ASCII only
            'viseroy_trap': ['{', '{', '{', '#', '%', '&', '{'],  # Animation for Viseroy trap crushing effect
            # MARROW CONDENSER animations
            'marrow_condenser_attack': ['/', '|', '\\', '-', '8', '$', 'O', '#', '*'],  # Swinging and striking with bone chunks
            'ossify': ['#', '%', '@', '*', '+', '=', '&', '$', '#', '/', '\\', '|', '-', '.'],  # ASCII bone hardening animation
            'marrow_dike': ['|', '|', '|', '|', '|', '|', '|', '#', '#'],  # Marrow wall forming - hash wall animation
            'slough': ['#', '*', '+', 'X', '*', '.'],  # Bone shards launching outward
            'site_inspection': ['#', 'O', '#', 'O', '#'],  # Animation for Site Inspection with eye-like symbols
            'expedite_rush': ['{', '<', '[', '{'],  # Animation for Expedite rush movement
            'expedite_impact': ['!', '!', '#', 'X', '*', '.'],  # Animation for Expedite impact
            'delta_config': ['Ψ', '.', ':', '=', ' ', '=', ':', '.', 'Ψ'],  # Teleportation effect
            'teleport_out': ['Ψ', '.', ':', '=', ' '],  # Teleport out animation
            'teleport_in': [' ', '=', ':', '.', 'Ψ'],  # Teleport in animation
            'estrange': ['~', '=', '=', '~', '-', '-', '~', '='],  # Dramatic pulsing beam
            'grae_exchange': ['/', '_', '*', 'ψ', 'Ψ'],  # Echo creation effect
            'marrow_healing': ['<', '3', '<', '3', '<', '+', '+', '*'],  # Blood plasma healing animation
            
            # FOWL_CONTRIVANCE reworked animations - rail artillery platform
            'fowl_contrivance_attack': ['T', '=', '-', '>', '*', '#', '@'],  # Rail cannon charging and firing
            'gaussian_charge': ['=', '=', '=', '=', '=', '=', '='],  # Charging rail cannon animation
            'gaussian_fire': ['=', '-', '-', '=', '>', '<', '='],  # Firing rail shot animation
            
            # Critical health "wretch" animation - displayed when units reach critical health
            'wretch': [
                '!', '?', '@', '#', '$', '%', '&', '*', 
                '?', '!', '*', '~', '+', '-', 'x', '/'
            ],
            
            # FOWL CONTRIVANCE reworked skills animations
            'gaussian_dusk_charging': ['~', '=', '=', '*', '+', 'O', '#', 'W'],  # Steam and energy buildup
            'gaussian_dusk_firing': ['*', '#', '@', '~', '.', ' '],  # Beam trail
            'parabol_launch': ['o', 'O', '0', '*'],  # Mortar shells ascending  
            'parabol_impact': ['*', '#', '@', '%', '~', '.'],  # Explosions and smoke
            'fragcrest_burst': ['.', ':', '*', '+', '#', 'x'],  # Fragmentation spread
            
            # FOWL CONTRIVANCE enemy impact animations
            'gaussian_dusk_impact': ['>', '!', '*', '#', '%', '~', '.'],  # Hypersonic projectile impact
            'parabol_unit_impact': ['*', '@', '#', '%', '&', '+', '.'],  # Mortar shell impact on unit
            'fragcrest_unit_impact': ['x', '+', '*', '#', '.'],  # Fragmentation impact on unit
            'rail_explosion_impact': ['!', '@', '#', '*', '+', '.'],  # Rail network death explosion impact
            
            # GAS_MACHINIST animations
            'gas_machinist_attack': ['o', 'O', 'o'],  # Gas bubble attack
            'summon_vapor': ['~', 'o', 'O', 'O'],  # Generic vapor formation
            'broaching_gas': ['~', '*', 'O'],  # Broaching Gas animation
            'saft_e_gas': ['~', 'o', '#'],  # Saft-E-Gas animation
            'diverge': ['*', '+', 'x', '#', '@'],  # Diverge animation
            'vapor_broaching': ['~', '*', '+'],  # Broaching Gas effect
            'vapor_safety': ['~', 'o', 'O'],  # Safety Gas effect
            'vapor_coolant': ['~', '*', '+'],  # Coolant Gas effect
            'vapor_cutting': ['~', '%', '#'],  # Cutting Gas effect
            'coolant_gas': ['~', '*', 'S'],  # Coolant Gas formation from Diverge
            'cutting_gas': ['~', '*', '%'],  # Cutting Gas formation from Diverge
            'cleanse': ['*', '+', 'o', '.'],  # Status effect cleansing animation
            'reform': [' ', '.', ':', 'o', 'O', 'M'],  # Gas Machinist reformation

            # DELPHIC_APPRAISER animations
            'delphic_appraiser_attack': ['$', '$', '$'],  # Basic attack with currency symbols
            'interferer_attack': ['x', '+', '*', 'x'],  # Plutonium carabiner cross attack

            # POTPOURRIST animations
            'potpourrist_attack': ['|', 'I', '!', '!', '*', '#', '@', '#', '*', '.'],  # Granite pedestal slam
            'melange_eminence': ['~', ',', '~', ':', '~', 'o', '~', ':', '~', ',', '~'],  # Potpourri petals and fumes wafting
            'melange_eminence_enhanced': ['~', ',', ':', 'o', '*', 'o', '@', 'o', '*', ':', ',', '~'],  # Enhanced potpourri flourish with more petals and aroma
            'demilune_sweep': ['/', '|', '\\', '-', '*'],  # Granite pedestal sweeping arc motion
            'infuse': [',', '.', ':', '*', 'o', 'O', '@', '#', '@', 'O', 'o', '*', ':', '.', ',', '~'],  # Whipping up potpourri blend
            'lunacy_moon': ['(', ' ', '(', ' ', '(', ' ', '(', ' ', '('],  # Rapid flashing crescent (Lunacy)
            'granite_geas_windup': ['.', ':', '|', 'I', '^', '^', '^', '|', 'I', '!', ':', '.'],  # Granite Geas windup - POTPOURRIST raising high, pausing, then SLAMMING
            'granite_geas_impact': ['*', '#', '@', '#', '*', '.'],  # Granite Geas impact - effect on target
            'geas_binding': [',', '.', ':', '|', 'I', '#', '#', '0', '0'],  # Geas binding - potpourri oils dripping down and sealing the magical obligation
            'geas_break': ['0', 'O', 'o', '.', '~', '~', '~'],  # Geas breaking - binding shatters and energy returns to POTPOURRIST


            # Market Futures: Appraiser reaches → spiral projections → furniture transforms → glow → anchor
            'market_futures': ['A', '|', '-', '#', '\\', '|', '/', '-', '#', '&', '%', '@', '$', '.', '*', '+', '*', '.', '~', '-', '=', 'T', '@'],

            # Market Teleport: Ally converted to golden arrows arcing through air
            'market_teleport': ['$', '^', '>', 'v', 'v', '*', 'A'],

            # Auction Curse: Podiums ascend → auctioneers rise → paddles raised → curse descends
            'auction_curse': ['.', '_', '=', 'i', 'I', 'Y', 'T', '~', '*', 'v', 'V', '@'],


            # Divine Depreciation: Downward valuation, furniture value drops, floor sinks
            'divine_depreciation': ['A', 'v', '9', '6', '3', '0', '_', '.', ' '],
            
            # INTERFERER animations
            'scalar_node_detonation': ['~', '~', '*', '#', '@', '+', '*', '~', '.']  # Standing wave collapse
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
            UnitType.MARROW_CONDENSER: 'assets/sprites/marrow_condenser.png',
            UnitType.FOWL_CONTRIVANCE: 'assets/sprites/fowl_contrivance.png',
            UnitType.GAS_MACHINIST: 'assets/sprites/gas_machinist.png',
            UnitType.HEINOUS_VAPOR: 'assets/sprites/heinous_vapor.png',
            UnitType.DELPHIC_APPRAISER: 'assets/sprites/delphic_appraiser.png',
            UnitType.DERELICTIONIST: 'assets/sprites/derelictionist.png',
            UnitType.INTERFERER: 'assets/sprites/interferer.png',
            UnitType.POTPOURRIST: 'assets/sprites/potpourrist.png'
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
            'marrow_wall': 'assets/tiles/marrow_wall.png',
            # Stained Stones map terrain
            'tiffany_lamp': 'assets/tiles/tiffany_lamp.png',
            'stained_stone': 'assets/tiles/stained_stone.png',
            'easel': 'assets/tiles/easel.png',
            'sculpture': 'assets/tiles/sculpture.png',
            'bench': 'assets/tiles/bench.png',
            'podium': 'assets/tiles/podium.png',
            'vase': 'assets/tiles/vase.png'
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
            'marrow_condenser_attack': 'assets/effects/bone.png',
            'fowl_contrivance_attack': 'assets/effects/fowl.png',
            'gas_machinist_attack': 'assets/effects/gas.png',
            'heinous_vapor_attack': 'assets/effects/vapor.png',
            'delphic_appraiser_attack': 'assets/effects/evaluation.png',
            'interferer_attack': 'assets/effects/radiation.png',
            'potpourrist_attack': 'assets/effects/pedestal.png'
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
            'judgement': ['judgement_1.png', 'judgement_2.png', 'judgement_3.png', 'judgement_4.png'],
            'judgement_critical': ['judgement_critical_1.png', 'judgement_critical_2.png', 'judgement_critical_3.png'],
            'expedite_rush': ['expedite_rush_1.png', 'expedite_rush_2.png', 'expedite_rush_3.png'],
            'expedite_impact': ['expedite_impact_1.png', 'expedite_impact_2.png', 'expedite_impact_3.png'],
            'grayman_attack': ['grayman_attack_1.png', 'grayman_attack_2.png', 'grayman_attack_3.png'],
            'delta_config': ['delta_config_1.png', 'delta_config_2.png', 'delta_config_3.png', 'delta_config_4.png'],
            'estrange': ['estrange_1.png', 'estrange_2.png', 'estrange_3.png'],
            'grae_exchange': ['grae_exchange_1.png', 'grae_exchange_2.png', 'grae_exchange_3.png'],
            # MARROW_CONDENSER animations
            'marrow_condenser_attack': ['marrow_attack_1.png', 'marrow_attack_2.png', 'marrow_attack_3.png'],
            'ossify': ['ossify_1.png', 'ossify_2.png', 'ossify_3.png'],
            'marrow_dike': ['marrow_dike_1.png', 'marrow_dike_2.png', 'marrow_dike_3.png'],
            'slough': ['slough_1.png', 'slough_2.png', 'slough_3.png'],
            # FOWL_CONTRIVANCE reworked animations
            'fowl_contrivance_attack': ['fowl_attack_1.png', 'fowl_attack_2.png', 'fowl_attack_3.png'],
            'gaussian_dusk_charging': ['gaussian_charge_1.png', 'gaussian_charge_2.png', 'gaussian_charge_3.png'],
            'gaussian_dusk_firing': ['gaussian_fire_1.png', 'gaussian_fire_2.png', 'gaussian_fire_3.png'],
            'parabol_launch': ['arc_launch_1.png', 'arc_launch_2.png', 'arc_launch_3.png'],
            'parabol_impact': ['arc_impact_1.png', 'arc_impact_2.png', 'arc_impact_3.png'],
            'fragcrest_burst': ['frag_burst_1.png', 'frag_burst_2.png', 'frag_burst_3.png'],
            'wretch': ['wretch_1.png', 'wretch_2.png', 'wretch_3.png', 'wretch_4.png', 'wretch_5.png', 'wretch_6.png']
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
            UnitType.MARROW_CONDENSER: 'marrow_condenser_attack',
            UnitType.FOWL_CONTRIVANCE: 'fowl_contrivance_attack',
            UnitType.GAS_MACHINIST: 'gas_machinist_attack',
            UnitType.HEINOUS_VAPOR: 'heinous_vapor_attack',
            UnitType.DELPHIC_APPRAISER: 'delphic_appraiser_attack',
            UnitType.INTERFERER: 'interferer_attack',
            UnitType.POTPOURRIST: 'potpourrist_attack'
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
            UnitType.MARROW_CONDENSER: 'marrow_condenser_attack',
            UnitType.FOWL_CONTRIVANCE: 'fowl_contrivance_attack',
            UnitType.GAS_MACHINIST: 'gas_machinist_attack',
            UnitType.HEINOUS_VAPOR: 'heinous_vapor_attack',
            UnitType.DELPHIC_APPRAISER: 'delphic_appraiser_attack',
            UnitType.POTPOURRIST: 'potpourrist_attack'
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
