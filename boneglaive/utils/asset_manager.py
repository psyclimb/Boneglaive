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
        """Initialize assets (character tiles and animation sequences)."""
        # Assets are character/glyph based; the graphical renderer derives its
        # own sprites and animations separately via the GameStateAdapter pipeline.
        self._initialize_text_assets()
    
    def _initialize_text_assets(self) -> None:
        """Initialize text-based assets (ASCII/Unicode characters)."""
        from boneglaive.utils.constants import UNIT_SYMBOLS
        self.unit_tiles = dict(UNIT_SYMBOLS)
        
        # Terrain symbols
        self.terrain_tiles = {
            'empty': '.',
            'wall': '#',
            'water': '~',
            'forest': '^',
            'limestone': '#',  # Limestone powder piles use hash symbol
            'dust': ',',       # Light limestone dusting use a comma
            'pillar': 'O',     # Pillars use capital O
            'radio_console': '%',  # Vintage radio console (speaker grills/dials)
            'coat_rack': 'Y',  # Coat rack uses Y
            'ottoman': 'u',    # Ottoman cushioned seating
            'console': '=',    # Console table (flat surface)
            'curiosity_shelf': 'E',  # Victorian curiosity shelf (stacked shelves)
            'marrow_wall': '#',  # Marrow Dike wall uses hash character
            'rail': '+',      # Rail track uses cross symbol for intersections
            'rail_junction': '┼',  # Upgraded rail junctions (Rail Genesis upgrade)
            # Stained Stones map terrain
            'tiffany_lamp': 'i',  # Tiffany lamp (lamp post shape)
            'stained_stone': '#',  # Full block for stained stone formations  
            'easel': 'h',      # Lowercase h resembles easel frame with crossbar
            'sculpture': '*',   # Sculpture (decorative art piece)
            'bench': 'n',      # Lowercase n resembles bench with legs
            'podium': '^',     # Elevated podium platform
            'vase': 'v',       # Lowercase v resembles vase shape
            'canyon_floor': '.',  # Canyon floor sediment
            # Hard Pressed map terrain - Industrial warehouse converted to home
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
            'melange_fume': '~',   # Tilde for aromatic fumes
            'derelict_building': '&',  # Ampersand for old decrepit building walls
            'slag_wall': '#',  # Hash for slag walls (same as other walls)
            'topiary': '&',  # Ampersand for topiary sculptures
            # Verdant Terrace map terrain
            'undergrowth': ',',    # Comma for lush jungle floor (like dust)
            'pylon': '#',          # Hash for concrete pylon (like other blockers)
            'sundial': 'o',        # Lowercase o for circular sundial face
            'fire_pit': 'w',       # Lowercase w for flames
            'granite_sphere': 'O', # Capital O for large round sphere
            'terracotta': 'U',     # Capital U for planter shape
            'lithophone': '=',     # Equals sign for flat stone slab
            'rattan_chair': 'h',   # Lowercase h for chair silhouette
            'flagstone': '.'       # Period for paved terrace floor (like other floors)
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
            'autoclave_steam': ['~', '≈', '=', '-', '/', '\\', '|', '+', 'x', '*'],  # Steam jets with spinning glaives
            'pry_range1': ['/', '|', '\\', '_', '-', '^'],  # Close-range prying motion with similar visual language to extended range
            'pry_range2': ['-', '\\', '_', '_', '_', '/'],  # Extended range prying motion - similar to extended attack
            'pry_launch': ['-', '/', '|', 'I', 'i', '^', '.', ' '],  # Unit being pried from horizontal to vertical, then diminishing as it launches upward
            'pry_impact': ['v', 'V', '@', '*', '.'],  # Unit falling back down with heavy impact
            'pry_debris': ['@', '#', '*', '+', '.'],  # Large chunks of debris falling straight down
            'vault': ['^', '^', '^', '^', '^'],  # Vault initiation animation - upward movement
            'vault_impact': ['v', 'v', 'V', '*', '.'],  # Vault landing animation
            'vault_impact_upgraded': ['V', 'X', '*', '#', '@', '#', '*', '+', '.'],  # Upgraded vault landing with shockwave
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

            # Delta Config upgrade animations - electromagnetic well abduction
            'delta_config_well_expand': ['.', ':', 'o', 'O', '0', '@'],  # Well expansion around GRAYMAN
            'delta_config_well_travel': ['~', '~', '~', '~'],  # Electromagnetic waves during travel
            'delta_config_well_collapse': ['@', '0', 'O', 'o', ':', '.', ' '],  # Well collapse at destination

            'estrange': ['~', '=', '=', '~', '-', '-', '~', '='],  # Dramatic pulsing beam
            'grae_exchange_ritual': ['|', '.', '|', '.', '|', '.'],  # GRAYMAN tapping cane on ground
            'grae_exchange_void': ['~', ':', '≈', '∼'],  # Reality distortion beam to target
            'grae_exchange_banish': ['@', '*', ':', '.', ' '],  # Target dissolving into void
            'grae_exchange_manifest': [' ', '.', ':', 'ψ', 'Ψ'],  # Echo materializing
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
            'scalar_node_detonation': ['~', '~', '*', '#', '@', '+', '*', '~', '.'],  # Standing wave collapse

            # LANDSCAPER animations
            'landscaper_attack': ['Y', '/', 'Y', '\\', 'Y', '/', 'Y', '\\'],  # Four tuning fork strikes in rapid succession
            'hornswoggle_wave': ['~', '=', '>', '>', '*'],  # Sonic wave traveling outward
            'hornswoggle_grab': ['*', '#', '!', '#', '*'],  # Terrain being ripped from ground
            'hornswoggle_drag': ['=', '#', '=', '#', '='],  # Terrain flying through air leaving slag
            'hornswoggle_deposit': ['V', '#', 'O', '#', '.'],  # Terrain slamming down at destination
            'topiary_breath_charge': ['(', '(', ')', ')', '(', ')'],  # Horn array resonating
            'topiary_breath_blast': ['~', '~', '>', '>', '*', '&'],  # Petrifying wave expanding
            'topiary_transform': ['@', '%', '&', '&', '&'],  # Unit crystallizing into topiary sculpture
            'topiary_revert': ['&', '%', '@', '*', '.'],  # Topiary crumbling back to unit
            'dissonance_windup': ['Y', 'Y', 'Y', 'Y'],  # Acoustic gyre forming
            'dissonance_strike': ['!', '#', 'X', '*', '+'],  # Gyre impacts terrain, shattering it
            'dissonance_shrapnel': ['*', '+', 'x', '.'],  # Debris fragments flying outward
            'slag_forming': ['~', '=', '#', '#'],  # Molten slag cooling into wall
            'slag_crumble': ['#', '%', '*', '.', ' ']  # Slag wall decaying and crumbling
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
            UnitType.POTPOURRIST: 'potpourrist_attack',
            UnitType.LANDSCAPER: 'landscaper_attack'
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
            UnitType.POTPOURRIST: 'potpourrist_attack',
            UnitType.LANDSCAPER: 'landscaper_attack'
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
