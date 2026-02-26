#!/usr/bin/env python3
"""
Graphical Renderer
Main pygame renderer for Boneglaive graphical version.
"""
import pygame
import sys
import os
import math
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add parent directory to path to import animations
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .animations import (
    Particle, ParticleEmitter, AnimatedUnit, FloatingText, DebrisParticle,
    AnimationFactory, LightningBolt
)
from .animations.core import (
    TILE_SIZE, COLOR_PLAYER1, COLOR_PLAYER2, COLOR_DAMAGE, COLOR_HEAL, COLOR_SKILL
)

from .game_state import GameStateAdapter, AnimationEvent
from .camera import Camera
from .ui.skill_bar import SkillBar
from .ui.combat_log import CombatLog
from .ui.message_log_window import MessageLogWindow
from .ui.status_effects import StatusEffectsPanel
from .ui.unit_info import UnitInfoPanel
from .ui.top_bar import TopBar
from .ui.unit_status_bar import UnitStatusBar
from .ui.action_menu import ActionMenu
from .ui.motor_animation import MotorAnimation
from .ui.help_page import HelpPage
from .ui.respawn_window import RespawnWindow
from .ui.upgrade_window import UpgradeWindow
from .ui.setup_window import SetupWindow
from .ui.setup_unit_help import SetupUnitHelp
from .ui.game_over_window import GameOverWindow
from .ui.concede_dialog import ConcedeDialog
from .ui_adapter import GraphicalUIAdapter

# Import TerrainType for terrain/furniture rendering
from boneglaive.game.map import TerrainType

# Import UnitType for Rail Genesis junction checking
from boneglaive.utils.constants import UnitType

# Import global message log for combat log sync
from boneglaive.utils.message_log import message_log

# Import config manager for UI layout settings
from boneglaive.utils.config import ConfigManager


# Screen constants (must match menu system)
SCREEN_WIDTH = 1480
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Boneglaive"

# Layout constants - Dedicated panel design (no overlays)
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 80
LEFT_PANEL_WIDTH = 280  # Dedicated left panel
RIGHT_PANEL_WIDTH = 280  # Dedicated right panel
GAME_BOARD_WIDTH = SCREEN_WIDTH - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH  # 920px

# Grid constants - Match game map size (20 cols x 10 rows)
GRID_WIDTH = 20
GRID_HEIGHT = 10
# Tiles scaled to fit in dedicated game board area
TILE_SIZE = GAME_BOARD_WIDTH // GRID_WIDTH  # 920 / 20 = 46px per tile
GAME_BOARD_HEIGHT = GRID_HEIGHT * TILE_SIZE  # 10 * 46 = 460px

# Grid positioned in center area (after left panel)
GRID_OFFSET_X = LEFT_PANEL_WIDTH  # 280px - right after left panel
GRID_OFFSET_Y = TOP_BAR_HEIGHT + ((SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT - GAME_BOARD_HEIGHT) // 2)  # Centered vertically

# Colors
COLOR_BG = (40, 44, 52)
COLOR_GRID_DARK = (50, 54, 62)
COLOR_GRID_LIGHT = (60, 64, 72)
COLOR_SELECTION = (100, 200, 255)
COLOR_TARGET = (255, 100, 100)
COLOR_MOVEMENT = (100, 255, 100)

# Skills that must animate BEFORE game logic executes (to show effects before displacement)
PRE_EXECUTION_BLOCKING_SKILLS = [
    "Fragcrest", "FRAGCREST",
    "Parabol", "PARABOL", "BIG_ARC",
    "Gaussian Dusk", "GAUSSIAN_DUSK",
    "Gaussian Dusk Charge", "GAUSSIAN_DUSK_CHARGE",
    "Gaussian Dusk Fire", "GAUSSIAN_DUSK_FIRE",
    "Pry", "PRY",
    # NOTE: Judgement removed from pre-execution so it plays AFTER moves execute
    "Autoclave", "AUTOCLAVE",
    "Matador", "MATADOR",
    "Poach", "POACH",
    "Vault_Upgraded", "VAULT_UPGRADED",  # Upgraded Vault with AOE landing impact
    # NOTE: Jawline removed - it doesn't displace units, so it should play AFTER moves execute
]


class GraphicalRenderer:
    """
    Main renderer for graphical Boneglaive.
    Manages pygame window, rendering, and coordination with game state.
    """

    def __init__(self, game_adapter: GameStateAdapter = None):
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()

        # Fonts - use Arial (most widely available across all platforms)
        try:
            self.font = pygame.font.SysFont('arial', 22)
            self.small_font = pygame.font.SysFont('arial', 16)
            self.large_font = pygame.font.SysFont('arial', 32)
        except:
            # Fallback to default if Arial not available
            self.font = pygame.font.Font(None, 22)
            self.small_font = pygame.font.Font(None, 16)
            self.large_font = pygame.font.Font(None, 32)

        # Camera system (centralizes coordinate conversion)
        self.camera = Camera(
            grid_offset_x=GRID_OFFSET_X,
            grid_offset_y=GRID_OFFSET_Y,
            tile_size=TILE_SIZE
        )

        # Game state adapter
        self.game_adapter = game_adapter or GameStateAdapter()

        # Visual elements
        self.units: List[AnimatedUnit] = []
        self.particles: List[Particle] = []
        self.particle_emitter = ParticleEmitter()
        self.floating_texts: List[FloatingText] = []
        self.debris_particles: List[DebrisParticle] = []

        # Active animations (skill animations, projectiles, etc.)
        self.active_animations = []  # List of animation objects

        # Background animations (persistent zones, environmental effects - NON-BLOCKING)
        # These don't prevent pending animations from flushing
        self.background_animations = []

        # Pending animation events (damage/heal numbers to show after animations finish)
        self.pending_animation_events = []

        # Visual effects
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.flash_alpha = 0
        self.flash_duration = 0
        self.flash_color = (255, 255, 255)

        # Input state
        self.hovered_grid_pos: Optional[Tuple[int, int]] = None
        self.selected_unit: Optional[AnimatedUnit] = None

        # UI state
        self.show_movement_range = False
        self.show_target_range = False
        self.show_skill_range = False
        self.show_skills = False  # Whether skill bar should be visible
        self.valid_positions: List[Tuple[int, int]] = []
        self.attack_positions: List[Tuple[int, int]] = []
        self.skill_positions: List[Tuple[int, int]] = []
        self.selected_skill = None

        # Astral value display state
        self.show_astral_values = False
        self.astral_value_pulse_time = 0

        # PERFORMANCE: Cache astral value fonts to avoid creating them every frame
        self._astral_value_font_cache = {}  # size -> font

        # Imbued furniture sparkles (for Market Futures)
        self.imbued_sparkles = []

        # UI Components
        self.top_bar = TopBar(self.font, self.small_font, self.large_font)
        self.unit_status_bar = UnitStatusBar(self.font, self.small_font)
        self.skill_bar = SkillBar(self.font, self.small_font)
        self.combat_log = CombatLog(self.small_font)
        self.message_log_window = MessageLogWindow(self.font, self.small_font)
        self.status_effects_panel = StatusEffectsPanel(self.font, self.small_font)
        self.unit_info_panel = UnitInfoPanel(self.font, self.small_font, self.large_font)
        self.action_menu = ActionMenu(self.font, self.small_font)
        self.motor_animation = MotorAnimation()
        self.help_page = HelpPage(self.font, self.small_font)
        self.respawn_window = RespawnWindow(self.font, self.small_font)
        self.upgrade_window = UpgradeWindow(self.font, self.small_font)
        self.setup_window = SetupWindow(self.font, self.small_font)
        self.setup_unit_help = SetupUnitHelp(self.font, self.small_font)
        self.game_over_window = GameOverWindow(self.font, self.small_font, self.large_font)
        self.concede_dialog = ConcedeDialog(self.font, self.small_font)

        # Track current action mode for top bar display
        self.current_action_mode = "SELECT"

        # Game over state
        self.return_to_menu = False

        # Respawn state
        self.respawn_mode = False
        self.respawn_selecting_unit = False
        self.respawn_selecting_location = False
        self.selected_dead_unit = None
        self.respawn_valid_tiles = []
        self.respawn_ghost_pos = None  # Grid position for ghost preview

        # Setup phase state
        self.setup_mode = False
        self.setup_selecting_unit = False
        self.setup_placing_unit = False
        self.selected_unit_type = None
        self.setup_ghost_pos = None  # Grid position for ghost preview
        self.setup_valid_tiles = []

        # UI Adapter for animations
        self.ui_adapter = GraphicalUIAdapter(self)

        # Terrain and furniture tile cache
        self.terrain_tiles: Dict[TerrainType, pygame.Surface] = {}
        self._init_terrain_furniture_mapping()

        # Universal rail bomb overlay (single graphic for all rail tiles)
        self.rail_universal: Optional[pygame.Surface] = None
        self._load_rail_overlays()

        # Scalar node trap overlay (revealed INTERFERER traps)
        self.scalar_node_trap: Optional[pygame.Surface] = None
        self.fragcrest_trap: Optional[pygame.Surface] = None
        self._load_scalar_node_overlay()
        self._load_fragcrest_trap_overlay()

        # Rail Genesis junction overlay (for upgraded FOWL_CONTRIVANCE)
        self.rail_junction_overlay: Optional[pygame.Surface] = None
        self.junction_pulse_time = 0
        self._load_rail_junction_overlay()

        # Performance: Pre-create reusable surfaces to avoid allocations every frame
        self._main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._indicator_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self._left_panel_surface = pygame.Surface((LEFT_PANEL_WIDTH, SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT))
        self._right_panel_surface = pygame.Surface((RIGHT_PANEL_WIDTH, SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT))
        self._flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Cached grid surface (to avoid redrawing 200 tiles every frame)
        self._grid_surface = pygame.Surface((GAME_BOARD_WIDTH, GAME_BOARD_HEIGHT))

        # Cache for sparkle surfaces (different sizes)
        self._sparkle_surf_cache: Dict[int, pygame.Surface] = {}

        # OPTIMIZATION: Dirty rectangle system for grid rendering
        self._static_grid_surface = None  # Cached full grid render
        self._dirty_tiles = set()  # Set of (x, y) tiles that need redrawing
        self._grid_fully_dirty = True  # Flag to force full redraw

        # FPS counter (for troubleshooting)
        self.show_fps = True  # Set to False to hide FPS counter
        self.fps_values = []  # Rolling window of recent FPS values
        self.fps_display = 0  # Smoothed FPS to display

        # Cached surfaces for performance (avoid creating SRCALPHA surfaces every frame)
        self._selection_highlight_cache = None
        self._last_selection_alpha = None

        self.running = True
        self.paused = False

    def setup_demo_scene(self):
        """
        Set up a demo scene with test units.
        For initial testing before game logic is hooked up.
        """
        # Create test units
        player_unit = AnimatedUnit(
            "GLAIVEMAN", player=0,
            grid_x=2, grid_y=4,
            color=COLOR_PLAYER1
        )
        player_unit.max_hp = 20
        player_unit.hp = 20

        enemy_unit = AnimatedUnit(
            "ENEMY", player=1,
            grid_x=9, grid_y=4,
            color=COLOR_PLAYER2
        )
        enemy_unit.max_hp = 15
        enemy_unit.hp = 15

        self.units = [player_unit, enemy_unit]

    def _init_terrain_furniture_mapping(self):
        """Initialize the mapping from TerrainType to SVG file paths."""
        # Mapping from TerrainType to SVG filename
        self.terrain_svg_map = {
            # Terrain types
            TerrainType.LIMESTONE: "graphics/terrain/limestone.svg",
            TerrainType.DUST: "graphics/terrain/dust.svg",
            TerrainType.PILLAR: "graphics/terrain/pillar.svg",
            TerrainType.MARROW_WALL: "graphics/terrain/marrow_wall.svg",
            # RAIL is now rendered as overlay in Pass 2, not as terrain tile
            TerrainType.STAINED_STONE: "graphics/terrain/stained_stone.svg",
            TerrainType.CANYON_FLOOR: "graphics/terrain/canyon_floor.svg",
            TerrainType.HYDRAULIC_PRESS: "graphics/terrain/hydraulic_press.svg",
            TerrainType.CONCRETE_FLOOR: "graphics/terrain/concrete_floor.svg",
            TerrainType.LEAF_PIT: "graphics/terrain/leaf_pit.svg",
            TerrainType.MELANGE_FUME: "graphics/terrain/melange_fume.svg",
            TerrainType.BLOOD_PLASMA: "graphics/terrain/blood_plasma.svg",

            # Furniture types
            TerrainType.RADIO_CONSOLE: "graphics/furniture/radio_console.svg",
            TerrainType.COAT_RACK: "graphics/furniture/coat_rack.svg",
            TerrainType.OTTOMAN: "graphics/furniture/ottoman.svg",
            TerrainType.CONSOLE: "graphics/furniture/console_table.svg",
            TerrainType.CURIOSITY_SHELF: "graphics/furniture/curiosity_shelf.svg",
            TerrainType.TIFFANY_LAMP: "graphics/furniture/tiffany_lamp.svg",
            TerrainType.EASEL: "graphics/furniture/easel.svg",
            TerrainType.SCULPTURE: "graphics/furniture/sculpture.svg",
            TerrainType.BENCH: "graphics/furniture/bench.svg",
            TerrainType.PODIUM: "graphics/furniture/podium.svg",
            TerrainType.VASE: "graphics/furniture/vase.svg",
            TerrainType.WORKBENCH: "graphics/furniture/workbench.svg",
            TerrainType.COUCH: "graphics/furniture/couch.svg",
            TerrainType.TOOLBOX: "graphics/furniture/toolbox.svg",
            TerrainType.COT: "graphics/furniture/cot.svg",
            TerrainType.CONVEYOR: "graphics/furniture/conveyor_belt.svg",
            TerrainType.MINI_PUMPKIN: "graphics/furniture/mini_pumpkin.svg",
            TerrainType.POTPOURRI_BOWL: "graphics/furniture/potpourri_bowl.svg",
        }

    def _load_terrain_tile(self, terrain_type: TerrainType) -> Optional[pygame.Surface]:
        """
        Load a terrain/furniture tile from SVG file.
        Caches the loaded surface for performance.

        Args:
            terrain_type: TerrainType enum value

        Returns:
            pygame.Surface or None if loading fails
        """
        # Check cache first
        if terrain_type in self.terrain_tiles:
            return self.terrain_tiles[terrain_type]

        # Get SVG path from mapping
        svg_path = self.terrain_svg_map.get(terrain_type)
        if not svg_path or not os.path.exists(svg_path):
            return None

        try:
            # Try to load SVG using cairosvg
            try:
                import cairosvg
                from io import BytesIO
                # Convert SVG to PNG in memory
                png_data = cairosvg.svg2png(url=svg_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
                surface = pygame.image.load(BytesIO(png_data))

                # Convert to alpha format to preserve transparency
                surface = surface.convert_alpha()

                # Cache the surface
                self.terrain_tiles[terrain_type] = surface
                return surface
            except ImportError:
                print(f"Info: cairosvg not available, cannot load terrain SVG: {svg_path}")
                return None
        except Exception as e:
            print(f"Warning: Could not load terrain SVG {svg_path}: {e}")
            return None

    def _load_rail_overlays(self) -> None:
        """
        Load universal rail bomb overlay graphic.
        This single explosive ordnance platform supports all cardinal directions.
        """
        svg_path = "graphics/terrain/rail_universal.svg"

        if not os.path.exists(svg_path):
            print(f"Warning: Universal rail overlay not found: {svg_path}")
            return

        try:
            import cairosvg
            from io import BytesIO
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=svg_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
            surface = pygame.image.load(BytesIO(png_data))

            # Set alpha for semi-transparent overlay effect
            surface = surface.convert_alpha()

            # Cache the universal rail surface
            self.rail_universal = surface
            print(f"Loaded universal rail bomb overlay")
        except ImportError:
            print(f"Info: cairosvg not available, cannot load universal rail overlay: {svg_path}")
        except Exception as e:
            print(f"Warning: Could not load universal rail overlay {svg_path}: {e}")

    def _load_scalar_node_overlay(self) -> None:
        """
        Load scalar node trap overlay graphic.
        This semi-transparent graphic shows revealed INTERFERER traps.
        """
        svg_path = "graphics/terrain/scalar_node_trap.svg"

        if not os.path.exists(svg_path):
            print(f"Warning: Scalar node trap overlay not found: {svg_path}")
            return

        try:
            import cairosvg
            from io import BytesIO
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=svg_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
            surface = pygame.image.load(BytesIO(png_data))

            # Set alpha for semi-transparent overlay effect
            surface = surface.convert_alpha()

            # Cache the scalar node trap surface
            self.scalar_node_trap = surface
            print(f"Loaded scalar node trap overlay")
        except ImportError:
            print(f"Info: cairosvg not available, cannot load scalar node trap overlay: {svg_path}")
        except Exception as e:
            print(f"Warning: Could not load scalar node trap overlay {svg_path}: {e}")

    def _load_fragcrest_trap_overlay(self) -> None:
        """
        Load Fragcrest trap overlay graphic.
        This semi-transparent graphic shows revealed FOWL CONTRIVANCE Fragcrest traps.
        Design: Hybrid between a claymore mine and a peacock tail.
        """
        svg_path = "graphics/terrain/fragcrest_trap.svg"

        if not os.path.exists(svg_path):
            print(f"Warning: Fragcrest trap overlay not found: {svg_path}")
            return

        try:
            import cairosvg
            from io import BytesIO
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=svg_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
            surface = pygame.image.load(BytesIO(png_data))

            # Set alpha for semi-transparent overlay effect
            surface = surface.convert_alpha()

            # Cache the fragcrest trap surface
            self.fragcrest_trap = surface
            print(f"Loaded Fragcrest trap overlay")
        except ImportError:
            print(f"Info: cairosvg not available, cannot load Fragcrest trap overlay: {svg_path}")
        except Exception as e:
            print(f"Warning: Could not load Fragcrest trap overlay {svg_path}: {e}")

    def _load_rail_junction_overlay(self) -> None:
        """
        Load Rail Genesis junction overlay graphic.
        This subtle graphic shows junction power-up locations for upgraded FOWL_CONTRIVANCE.
        """
        svg_path = "graphics/ui/rail_junction_overlay.svg"

        if not os.path.exists(svg_path):
            print(f"Warning: Rail junction overlay not found: {svg_path}")
            return

        try:
            import cairosvg
            from io import BytesIO
            # Convert SVG to PNG in memory
            png_data = cairosvg.svg2png(url=svg_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
            surface = pygame.image.load(BytesIO(png_data))

            # Set alpha for semi-transparent overlay effect
            surface = surface.convert_alpha()

            # Cache the rail junction overlay surface
            self.rail_junction_overlay = surface
            print(f"Loaded Rail Genesis junction overlay")
        except ImportError:
            print(f"Info: cairosvg not available, cannot load Rail Genesis junction overlay: {svg_path}")
        except Exception as e:
            print(f"Warning: Could not load Rail Genesis junction overlay {svg_path}: {e}")

    # ASCII renderer compatibility stubs
    def animate_attack_sequence(self, y, x, sequence, color, duration):
        """Stub for ASCII renderer compatibility. Graphical mode uses AnimationFactory instead."""
        pass

    def draw_damage_text(self, y, x, text, color, attrs=None):
        """Stub for ASCII renderer compatibility. Graphical mode uses FloatingText instead."""
        pass

    def refresh(self):
        """Stub for ASCII renderer compatibility. Graphical mode handles rendering differently."""
        pass

    def sync_units_from_game(self):
        """
        Synchronize visual units with game state.
        Creates visual units for game units that don't have them yet.
        Removes visual units for dead game units.
        """
        if not self.game_adapter.game:
            return

        # Get all alive game units
        alive_units = {}
        for game_unit in self.game_adapter.game.units:
            if game_unit.hp > 0:  # Unit is alive
                unit_id = self.game_adapter._get_unit_id(game_unit)
                alive_units[unit_id] = game_unit

        # Create visual units for new game units
        for unit_id, game_unit in alive_units.items():
            if unit_id not in self.game_adapter.visual_units:
                # Create new visual unit
                animated_unit = self._create_animated_unit_from_game(game_unit)
                self.units.append(animated_unit)

                # Register in adapter
                self.game_adapter.create_visual_unit(game_unit, animated_unit)

                # Check if this is a respawning unit (not a brand new unit or vapor)
                from boneglaive.utils.constants import UnitType
                is_vapor = hasattr(game_unit, 'type') and game_unit.type == UnitType.HEINOUS_VAPOR
                is_echo = hasattr(game_unit, 'is_echo') and game_unit.is_echo
                is_respawn = hasattr(game_unit, '_just_respawned') and game_unit._just_respawned

                # Trigger respawn animation ONLY for actual respawns (not vapors, echoes, or initial spawns)
                # Vapors and echoes have their own spawn animations
                if is_respawn and not is_vapor and not is_echo:
                    print(f"[Renderer] Respawned unit detected: {game_unit.type}, triggering respawn animation at ({game_unit.y}, {game_unit.x})")

                    # Create respawn animation IMMEDIATELY (not queued)
                    from boneglaive.graphical.animations import AnimationFactory
                    respawn_animation = AnimationFactory.create_animation(
                        "RESPAWN",
                        caster_unit=animated_unit,
                        target_unit=animated_unit,
                        target_pos=(game_unit.y, game_unit.x),
                        is_crit=False,
                        is_infused=False,
                        particle_emitter=self.particle_emitter,
                        debris_list=self.debris_particles,
                        screen_shake_callback=self.trigger_screen_shake,
                        screen_flash_callback=self.trigger_screen_flash,
                        units_list=self.units,
                        camera=self.camera,
                        game=self.game_adapter.game
                    )
                    if respawn_animation:
                        self.active_animations.append(respawn_animation)
                        print(f"  [Animation] Successfully triggered respawn animation for {game_unit.get_display_name()}")
                    else:
                        print(f"  [Animation] WARNING: Failed to create respawn animation")

                    # Clear the respawn flag after triggering animation
                    game_unit._just_respawned = False

                # If this is a HEINOUS VAPOR, trigger spawn animation
                if hasattr(game_unit, 'type') and game_unit.type == UnitType.HEINOUS_VAPOR:
                    vapor_type = getattr(game_unit, 'vapor_type', 'BROACHING')

                    # Trigger spawn animation for all vapor types at their actual positions
                    # For COOLANT and CUTTING, this plays after the Diverge split animation
                    if vapor_type in ['BROACHING', 'SAFETY', 'COOLANT', 'CUTTING', 'CALIBRATION', 'LIVING_AEROSOL']:
                        skill_name = f"{vapor_type}_gas"
                        print(f"[Renderer] New HEINOUS VAPOR detected: {vapor_type}, triggering spawn animation at ({game_unit.y}, {game_unit.x})")

                        # Queue spawn animation at the vapor's actual position
                        self.game_adapter.queue_skill_animation(
                            skill_name=skill_name,
                            caster=game_unit,
                            target=None,
                            skill_target=(game_unit.y, game_unit.x)  # Spawn position in game coords (y, x)
                        )

        # Remove visual units for dead game units
        dead_unit_ids = []
        for unit_id in self.game_adapter.visual_units.keys():
            if unit_id not in alive_units:
                dead_unit_ids.append(unit_id)

        for unit_id in dead_unit_ids:
            visual_unit = self.game_adapter.visual_units[unit_id]
            if visual_unit.animated_unit in self.units:
                self.units.remove(visual_unit.animated_unit)
            del self.game_adapter.visual_units[unit_id]

    def _get_sprite_path(self, unit_type) -> str:
        """
        Get the sprite path for a unit type.

        Args:
            unit_type: UnitType enum (int for DLC units)

        Returns:
            Path to sprite file (absolute path)
        """
        import os
        from pathlib import Path

        # Check if this is a DLC unit (enum value >= 100)
        unit_type_value = unit_type if isinstance(unit_type, int) else getattr(unit_type, 'value', unit_type)

        if isinstance(unit_type_value, int) and unit_type_value >= 100:
            # DLC unit - get unit_id from DLC manager
            from boneglaive.game.dlc_manager import get_dlc_manager
            dlc_manager = get_dlc_manager()
            unit_id = dlc_manager.get_unit_id_from_enum(unit_type_value)

            if unit_id:
                unit_type_name = unit_id.lower()
            else:
                # Fallback if not found
                unit_type_name = str(unit_type_value)
        else:
            # Base game unit - extract name from enum
            unit_type_name = str(unit_type).split('.')[-1].lower()

        # Try relative path first (from working directory)
        sprite_path = f"graphics/units/{unit_type_name}.svg"
        if os.path.exists(sprite_path):
            return os.path.abspath(sprite_path)

        # Try path relative to this file's location
        renderer_dir = Path(__file__).parent.parent  # Go up to boneglaive/
        absolute_path = renderer_dir / "graphics" / "units" / f"{unit_type_name}.svg"
        if absolute_path.exists():
            return str(absolute_path)

        # Try one more level up (project root)
        project_root = renderer_dir.parent
        absolute_path = project_root / "graphics" / "units" / f"{unit_type_name}.svg"
        if absolute_path.exists():
            return str(absolute_path)

        # Return relative path as fallback (will fail sprite load but won't crash)
        return sprite_path

    def _create_animated_unit_from_game(self, game_unit) -> AnimatedUnit:
        """
        Create an AnimatedUnit from a game Unit.

        Args:
            game_unit: Unit from game logic

        Returns:
            AnimatedUnit for rendering
        """
        # Determine color based on player
        color = COLOR_PLAYER1 if game_unit.player == 1 else COLOR_PLAYER2

        # Get unit type name for display
        unit_name = str(game_unit.type).split('.')[-1]  # Extract enum name

        # Get sprite path
        sprite_path = self._get_sprite_path(game_unit.type)

        # Create animated unit
        # Note: game uses (y, x), we need (grid_x, grid_y)
        # grid_x = x (column), grid_y = y (row)
        animated = AnimatedUnit(
            name=unit_name,
            player=game_unit.player,
            grid_x=game_unit.x,  # x is column
            grid_y=game_unit.y,  # y is row
            color=color,
            sprite_path=sprite_path,
            game_unit=game_unit  # Pass game unit for vapor type detection
        )

        # Set stats
        animated.max_hp = game_unit.max_hp
        animated.hp = game_unit.hp

        # Fix position to account for grid offset
        # AnimatedUnit calculates position as grid * TILE_SIZE + TILE_SIZE//2
        # but doesn't know about GRID_OFFSET, so we need to add it
        animated.x += GRID_OFFSET_X
        animated.y += GRID_OFFSET_Y
        animated.target_x = animated.x
        animated.target_y = animated.y

        return animated

    def screen_to_grid(self, screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """
        Convert screen coordinates to grid coordinates.

        Args:
            screen_x, screen_y: Screen pixel coordinates

        Returns:
            (grid_x, grid_y) or None if outside grid
        """
        grid_x = (screen_x - GRID_OFFSET_X) // TILE_SIZE
        grid_y = (screen_y - GRID_OFFSET_Y) // TILE_SIZE

        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            return (grid_x, grid_y)
        return None

    def grid_to_screen(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """
        Convert grid coordinates to screen pixel coordinates (center of tile).

        Args:
            grid_x, grid_y: Grid coordinates

        Returns:
            (screen_x, screen_y) pixel coordinates
        """
        screen_x = GRID_OFFSET_X + grid_x * TILE_SIZE + TILE_SIZE // 2
        screen_y = GRID_OFFSET_Y + grid_y * TILE_SIZE + TILE_SIZE // 2
        return (screen_x, screen_y)

    def get_unit_at_grid(self, grid_x: int, grid_y: int) -> Optional[AnimatedUnit]:
        """Get unit at grid position."""
        for unit in self.units:
            if unit.grid_x == grid_x and unit.grid_y == grid_y:
                return unit
        return None

    def get_unit_at_grid_or_ghost(self, grid_x: int, grid_y: int) -> Optional[AnimatedUnit]:
        """
        Get unit at grid position, checking both ghost positions (pending moves) and physical positions.
        Prioritizes ghosts over physical positions to allow issuing commands from future position.

        Args:
            grid_x, grid_y: Grid coordinates to check

        Returns:
            AnimatedUnit if found at position or with move_target to position, else None
        """
        # First check if any unit has a move_target (ghost) at this position
        for unit in self.units:
            game_unit = self._get_game_unit(unit)
            if game_unit and game_unit.move_target:
                # move_target is in game coords (y, x), convert to grid coords (x, y)
                target_y, target_x = game_unit.move_target
                if target_x == grid_x and target_y == grid_y:
                    return unit  # Return the unit whose ghost is at this position

        # No ghost found, check physical positions
        return self.get_unit_at_grid(grid_x, grid_y)

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONUP:
                # Handle scrollbar releases
                if event.button == 1:
                    self.help_page.handle_mouse_up()
                    self.setup_unit_help.handle_mouse_up()
                    self.setup_window.handle_mouse_up()
                    self.respawn_window.handle_mouse_up()

            elif event.type == pygame.KEYDOWN:
                # Check if concede dialog is open first (highest priority)
                if self.concede_dialog.visible:
                    action = self.concede_dialog.handle_key(event.key)
                    if action == "cancel":
                        self.concede_dialog.hide()
                    elif action == "concede":
                        self.confirm_concede()
                    # Ignore all other keys when concede dialog is open
                    continue

                # Check if game over window is open
                if self.game_over_window.visible:
                    action = self.game_over_window.handle_key(event.key)
                    if action == "menu":
                        self.return_to_main_menu()
                    elif action == "exit":
                        self.running = False
                    # Ignore all other keys when game over window is open
                    continue

                # Check if message log window is open
                if self.message_log_window.visible:
                    if event.key == pygame.K_ESCAPE:
                        self.message_log_window.hide()
                    elif event.key == pygame.K_UP:
                        self.message_log_window.handle_scroll(-1)
                    elif event.key == pygame.K_DOWN:
                        self.message_log_window.handle_scroll(1)
                    # Ignore all other keys when message log is open
                    continue

                # Check if upgrade window is open
                if self.upgrade_window.visible:
                    result = self.upgrade_window.handle_key(event.key)
                    if result == 'confirm':
                        upgrade = self.upgrade_window.get_selected_upgrade()
                        if upgrade:
                            game_unit = self.upgrade_window.unit
                            success = self.game_adapter.game.apply_unit_upgrade(game_unit, upgrade['skill_name'])
                            if success:
                                print(f"Upgraded {upgrade['skill_name']}!")
                                self.combat_log.add_message(f"Upgraded {upgrade['skill_name']}!", "system")
                                # Refresh the upgrade window with updated available upgrades
                                if not self.upgrade_window.show(game_unit):
                                    # No more upgrades available, close window
                                    self.upgrade_window.hide()
                                # Ignore all other keys when upgrade window is open
                                continue
                        self.upgrade_window.hide()
                    elif result == 'cancel':
                        self.upgrade_window.hide()
                    # Ignore all other keys when upgrade window is open
                    continue

                # Check if help page is open
                if self.help_page.visible:
                    if event.key == pygame.K_ESCAPE:
                        self.help_page.hide()
                    elif event.key == pygame.K_UP:
                        self.help_page.handle_scroll(-1)
                    elif event.key == pygame.K_DOWN:
                        self.help_page.handle_scroll(1)
                    # Ignore all other keys when help is open
                    continue

                # Handle respawn mode input
                if self.respawn_mode:
                    if self.respawn_selecting_unit:
                        # Unit selection phase
                        if event.key == pygame.K_ESCAPE:
                            self.exit_respawn_mode()
                        elif event.key == pygame.K_UP:
                            self.respawn_window.select_prev()
                        elif event.key == pygame.K_DOWN:
                            self.respawn_window.select_next()
                        elif event.key == pygame.K_RETURN:
                            self.confirm_respawn_unit_selection()
                    elif self.respawn_selecting_location:
                        # Location selection phase
                        if event.key == pygame.K_ESCAPE:
                            self.exit_respawn_mode()
                        elif event.key == pygame.K_RETURN:
                            self.confirm_respawn_location()
                    continue  # Ignore all other keys in respawn mode

                # Handle setup mode input (mouse-only, but allow ESC to exit)
                if self.setup_mode:
                    if self.setup_placing_unit:
                        # During placement, ESC returns to unit selection
                        if event.key == pygame.K_ESCAPE:
                            self.return_to_unit_selection()
                    # Ignore all other keys in setup mode
                    continue

                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_TAB:
                    # Cycle through player's units (SHIFT+TAB for backwards)
                    shift_pressed = pygame.key.get_mods() & pygame.KMOD_SHIFT
                    self._cycle_unit_selection(backwards=shift_pressed)

                # DEV KEYBIND: Add upgrade points with '=' key (temporary for testing)
                elif event.key == pygame.K_EQUALS:
                    if self.game_adapter and self.game_adapter.game:
                        game = self.game_adapter.game
                        if game.current_player == 1:
                            game.player1_upgrade_points += 1
                            print(f"[DEV] Player 1 upgrade points: {game.player1_upgrade_points}")
                        else:
                            game.player2_upgrade_points += 1
                            print(f"[DEV] Player 2 upgrade points: {game.player2_upgrade_points}")

                # Check action menu hotkeys first
                elif event.key in [pygame.K_m, pygame.K_a, pygame.K_s, pygame.K_u, pygame.K_r, pygame.K_t, pygame.K_c, pygame.K_h]:
                    action = self.action_menu.handle_hotkey(event.key)
                    if action:
                        self._handle_action_menu_click(action)

                # Then check skill hotkeys (only if skills are visible)
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                  pygame.K_q, pygame.K_w]:
                    # Handle skill hotkeys only if skill bar is visible
                    if self.show_skills:
                        skill = self.skill_bar.handle_hotkey(event.key)
                        if skill and self.selected_unit:
                            print(f"Skill selected: {skill.name}")
                            self.selected_skill = skill
                            self.current_action_mode = "SKILL"

                            # Query skill range
                            game_unit = self._get_game_unit(self.selected_unit)
                            if game_unit:
                                # If unit has pending move, calculate skill range from ghost position
                                if game_unit.move_target:
                                    original_y, original_x = game_unit.y, game_unit.x
                                    game_unit.y, game_unit.x = game_unit.move_target
                                    self.skill_positions = self.game_adapter.get_skill_range(game_unit, skill)
                                    game_unit.y, game_unit.x = original_y, original_x
                                else:
                                    self.skill_positions = self.game_adapter.get_skill_range(game_unit, skill)
                                print(f"Skill has {len(self.skill_positions)} valid targets")

                                # Hide movement/attack range, show skill range
                                self.show_movement_range = False
                                self.show_target_range = False
                                self.show_skill_range = True
                            else:
                                self.skill_positions = []
                        elif skill and not self.selected_unit:
                            print("Select a unit first to use skills")

            elif event.type == pygame.MOUSEMOTION:
                # Handle concede dialog mouse motion
                if self.concede_dialog.visible:
                    self.concede_dialog.handle_mouse_motion(event.pos)
                # Handle game over window mouse motion
                elif self.game_over_window.visible:
                    self.game_over_window.handle_mouse_motion(event.pos)
                # Handle help page scrollbar dragging
                elif self.help_page.visible:
                    self.help_page.handle_mouse_motion(event.pos)
                # Handle upgrade window mouse motion
                elif self.upgrade_window.visible:
                    self.upgrade_window.handle_mouse_motion(event.pos)
                # Handle respawn window mouse motion
                elif self.respawn_selecting_unit:
                    self.respawn_window.handle_mouse_motion(event.pos)
                    self.respawn_window.handle_mouse_drag(event.pos)
                # Handle respawn location preview
                elif self.respawn_selecting_location:
                    grid_pos = self.screen_to_grid(event.pos[0], event.pos[1])
                    if grid_pos:
                        self.respawn_ghost_pos = grid_pos
                # Handle setup window mouse motion
                elif self.setup_selecting_unit:
                    self.setup_window.handle_mouse_motion(event.pos)
                    self.setup_window.handle_mouse_drag(event.pos)
                    # Also update help panel for button hover and scrollbar dragging
                    self.setup_unit_help.handle_mouse_motion(event.pos)
                    self.setup_unit_help.handle_mouse_drag(event.pos)
                # Handle setup placement preview
                elif self.setup_placing_unit:
                    grid_pos = self.screen_to_grid(event.pos[0], event.pos[1])
                    if grid_pos:
                        self.setup_ghost_pos = grid_pos

                # Update hovered grid position
                self.hovered_grid_pos = self.screen_to_grid(event.pos[0], event.pos[1])

                # Update UI component hovers
                if self.show_skills:
                    self.skill_bar.handle_mouse_motion(event.pos)
                self.status_effects_panel.handle_mouse_motion(event.pos)
                self.unit_status_bar.handle_mouse_motion(event.pos)
                self.action_menu.handle_mouse_motion(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse wheel scrolling
                if event.button == 4:  # Scroll up
                    if self.message_log_window.visible:
                        self.message_log_window.handle_scroll(-1)
                    elif self.help_page.visible:
                        self.help_page.handle_scroll(-1)
                    elif self.setup_selecting_unit:
                        # Check if scrolling in help panel (when focused)
                        if hasattr(self, 'setup_help_panel_rect') and self.setup_unit_help.has_focus:
                            if self.setup_help_panel_rect and self.setup_help_panel_rect.collidepoint(event.pos):
                                self.setup_unit_help.handle_scroll(1)
                        else:
                            self.setup_window.handle_scroll(1)
                    elif self.respawn_selecting_unit:
                        # Add scroll support for respawn window too
                        pass
                elif event.button == 5:  # Scroll down
                    if self.message_log_window.visible:
                        self.message_log_window.handle_scroll(1)
                    elif self.help_page.visible:
                        self.help_page.handle_scroll(1)
                    elif self.setup_selecting_unit:
                        # Check if scrolling in help panel (when focused)
                        if hasattr(self, 'setup_help_panel_rect') and self.setup_unit_help.has_focus:
                            if self.setup_help_panel_rect and self.setup_help_panel_rect.collidepoint(event.pos):
                                self.setup_unit_help.handle_scroll(-1)
                        else:
                            self.setup_window.handle_scroll(-1)
                    elif self.respawn_selecting_unit:
                        # Add scroll support for respawn window too
                        pass
                elif event.button == 1:  # Left click
                    # Handle concede dialog clicks
                    if self.concede_dialog.visible:
                        action = self.concede_dialog.handle_mouse_click(event.pos)
                        if action == "cancel":
                            self.concede_dialog.hide()
                        elif action == "concede":
                            self.confirm_concede()
                    # Handle game over window clicks
                    elif self.game_over_window.visible:
                        action = self.game_over_window.handle_mouse_click(event.pos)
                        if action == "menu":
                            self.return_to_main_menu()
                        elif action == "exit":
                            self.running = False
                        continue

                    # Handle help page scrollbar clicks
                    if self.help_page.visible:
                        if self.help_page.handle_mouse_down(event.pos):
                            continue  # Scrollbar was clicked, don't process other clicks

                    # Handle upgrade window clicks (must be before other UI elements)
                    if self.upgrade_window.visible:
                        result = self.upgrade_window.handle_click(event.pos)
                        if result == 'confirm':
                            upgrade = self.upgrade_window.get_selected_upgrade()
                            if upgrade:
                                game_unit = self.upgrade_window.unit
                                success = self.game_adapter.game.apply_unit_upgrade(game_unit, upgrade['skill_name'])
                                if success:
                                    print(f"Upgraded {upgrade['skill_name']}!")
                                    self.combat_log.add_message(f"Upgraded {upgrade['skill_name']}!", "system")
                                    # Refresh the upgrade window with updated available upgrades
                                    if not self.upgrade_window.show(game_unit):
                                        # No more upgrades available, close window
                                        self.upgrade_window.hide()
                                    continue
                            self.upgrade_window.hide()
                            continue
                        elif result == 'cancel':
                            self.upgrade_window.hide()
                            continue
                        elif result == 'consumed':
                            # Click was on window but no action - just consume it
                            continue

                    # Check if clicking on combat log to open expanded view (only when not in setup mode)
                    if not self.setup_mode:
                        combat_log_x = LEFT_PANEL_WIDTH + 10
                        combat_log_y = GRID_OFFSET_Y + GAME_BOARD_HEIGHT + 10
                        combat_log_rect = pygame.Rect(combat_log_x, combat_log_y, 900, 90)
                        if combat_log_rect.collidepoint(event.pos):
                            # Open expanded message log
                            self.message_log_window.show(self.combat_log.messages)
                            continue

                    # Handle respawn window clicks
                    if self.respawn_selecting_unit:
                        # Check scrollbar first
                        if self.respawn_window.handle_mouse_down(event.pos):
                            continue
                        if self.respawn_window.handle_click(event.pos):
                            self.confirm_respawn_unit_selection()
                        continue
                    elif self.respawn_selecting_location:
                        # Click to confirm respawn location
                        self.confirm_respawn_location()
                        continue

                    # Handle setup window clicks
                    if self.setup_selecting_unit:
                        # Check if clicking scrollbars first
                        if self.setup_window.handle_mouse_down(event.pos):
                            # Setup window scrollbar was clicked
                            continue
                        if self.setup_unit_help.handle_mouse_down(event.pos):
                            # Help panel scrollbar was clicked
                            continue
                        # Check if clicking help panel first
                        if hasattr(self, 'setup_help_panel_rect') and self.setup_help_panel_rect:
                            if self.setup_help_panel_rect.collidepoint(event.pos):
                                # Clicked on help panel - handle it
                                if self.setup_unit_help.handle_click(event.pos):
                                    # Click was handled (e.g., button clicked)
                                    continue
                                # Give it focus
                                self.setup_unit_help.has_focus = True
                                continue

                        # Otherwise, handle setup window click
                        self.setup_unit_help.has_focus = False  # Remove focus from help panel
                        unit_selected, confirm_clicked, unit_type_to_place = self.setup_window.handle_click(event.pos)
                        if confirm_clicked:
                            # Confirm button was clicked - exit setup
                            self.confirm_setup_complete()
                        elif unit_type_to_place:
                            # User double-clicked a unit, start placement immediately
                            self.confirm_unit_type_selection()
                        elif unit_selected:
                            # Unit was selected, update help panel
                            display_unit = self.setup_window.get_display_unit()
                            self.setup_unit_help.update(display_unit)
                        continue
                    elif self.setup_placing_unit:
                        # Click to place unit at cursor position
                        self.confirm_unit_placement()
                        continue

                    # Check if clicking on UI components first
                    clicked_handled = False

                    # Check skill bar click (only if skills are visible)
                    if self.show_skills:
                        skill = self.skill_bar.handle_click(event.pos)
                        if skill and self.selected_unit:
                            print(f"Skill selected via click: {skill.name}")
                            self.selected_skill = skill
                            game_unit = self._get_game_unit(self.selected_unit)
                            if game_unit:
                                # Calculate skill range from ghost position if unit has pending move
                                if game_unit.move_target:
                                    original_y, original_x = game_unit.y, game_unit.x
                                    game_unit.y, game_unit.x = game_unit.move_target
                                    self.skill_positions = self.game_adapter.get_skill_range(game_unit, skill)
                                    game_unit.y, game_unit.x = original_y, original_x
                                else:
                                    self.skill_positions = self.game_adapter.get_skill_range(game_unit, skill)
                                self.show_movement_range = False
                                self.show_target_range = False
                                self.show_skill_range = True
                                self.current_action_mode = "SKILL"
                            clicked_handled = True

                    # Check unit status bar click
                    if not clicked_handled:
                        clicked_unit = self.unit_status_bar.handle_click(event.pos)
                        if clicked_unit:
                            # Select this unit
                            for visual_unit in self.units:
                                if (visual_unit.grid_x == clicked_unit.x and
                                    visual_unit.grid_y == clicked_unit.y):
                                    self.selected_unit = visual_unit
                                    self.skill_bar.update(visual_unit, clicked_unit)
                                    self.unit_info_panel.update(visual_unit, clicked_unit)
                                    self.status_effects_panel.update(clicked_unit)
                                    print(f"Selected unit: {clicked_unit.get_display_name()}")
                                    clicked_handled = True
                                    break

                    # Check action menu click
                    if not clicked_handled:
                        action = self.action_menu.handle_click(event.pos)
                        if action:
                            self._handle_action_menu_click(action)
                            clicked_handled = True

                    # If no UI clicked, check grid click
                    if not clicked_handled:
                        grid_pos = self.screen_to_grid(event.pos[0], event.pos[1])
                        if grid_pos:
                            self.handle_grid_click(grid_pos[0], grid_pos[1])

                elif event.button == 3:  # Right click
                    # Check if message log window is open first
                    if self.message_log_window.visible:
                        self.message_log_window.hide()
                        continue

                    # Cancel selection and skill mode
                    self.selected_unit = None
                    self.selected_skill = None
                    self.show_movement_range = False
                    self.show_target_range = False
                    self.show_skill_range = False
                    self.show_skills = False  # Hide skill bar
                    self.show_astral_values = False  # Hide astral values
                    self.valid_positions = []
                    self.attack_positions = []
                    self.skill_positions = []
                    self.skill_bar.update(None, None)
                    self.status_effects_panel.update(None)
                    self.unit_info_panel.update(None, None)
                    # Also clear furniture info if showing
                    self.unit_info_panel.furniture_info = None

                elif event.button == 4:  # Mouse wheel up
                    if self.help_page.visible:
                        self.help_page.handle_scroll(-1)

                elif event.button == 5:  # Mouse wheel down
                    if self.help_page.visible:
                        self.help_page.handle_scroll(1)

    def handle_grid_click(self, grid_x: int, grid_y: int):
        """
        Handle click on grid tile.

        Args:
            grid_x, grid_y: Grid coordinates clicked
        """
        # Check for units at this position (including ghosts from pending moves)
        unit = self.get_unit_at_grid_or_ghost(grid_x, grid_y)

        # Get current player from game
        current_player = self.game_adapter.game.current_player if self.game_adapter.game else 1

        # If awaiting target selection (for skills)
        if self.game_adapter.awaiting_target:
            # TODO: Execute skill on target
            self.game_adapter.handle_player_action(
                "target_skill",
                target_id=self._get_unit_id(unit) if unit else None
            )
            return

        # Check if we're in skill targeting mode
        if self.selected_skill and self.selected_unit:
            # Check if clicked position is in skill range
            if (grid_x, grid_y) in self.skill_positions:
                game_unit = self._get_game_unit(self.selected_unit)
                if game_unit:
                    # Use the skill (this calls skill.use() which sets indicators and queues the action)
                    target_pos = (grid_y, grid_x)  # Convert to game coords

                    # Call the skill's use() method to properly queue it and set indicators
                    success = self.selected_skill.use(game_unit, target_pos, self.game_adapter.game)

                    if success:
                        print(f"Skill planned: {self.selected_skill.name} at ({grid_y}, {grid_x})")

                        # Special handling for Parallax - it executes immediately, not during turn execution
                        if self.selected_skill.name == "Parallax":
                            print(f"[Renderer] Parallax executed immediately - triggering animation")

                            # Create animation event for immediate execution
                            from boneglaive.graphical.game_state import AnimationEvent
                            anim_event = AnimationEvent(
                                event_type="skill",
                                source_unit=game_unit,
                                target_unit=None,
                                skill_name="Parallax",
                                skill_target=target_pos,
                                is_infused=False
                            )

                            # Create skill animation IMMEDIATELY (don't queue it)
                            # This prevents it from being delayed by movement events
                            self._create_skill_animation(anim_event)

                            # Mark visual unit as teleporting to prevent walking animation
                            # visual_units dict is keyed by UUID, not id()
                            if hasattr(game_unit, 'uuid'):
                                visual_unit = self.game_adapter.visual_units.get(game_unit.uuid)
                                if visual_unit:
                                    visual_unit.pending_teleport_skill = "Parallax"
                                    print(f"[Renderer] Set pending_teleport_skill flag on visual unit")
                                else:
                                    print(f"[Renderer] WARNING: Could not find visual unit with UUID {game_unit.uuid}")
                            else:
                                print(f"[Renderer] WARNING: Game unit has no UUID!")

                            # Sync state to update visual unit position
                            sync_events = self.game_adapter.sync_state()
                            for event in sync_events:
                                if event.event_type != "skill":  # Skip skill events, we already handled it
                                    self.handle_animation_event(event)

                            print(f"[Renderer] Parallax animation triggered")

                        # Special handling for Deft(?) Reroll - it executes immediately, not during turn execution
                        if self.selected_skill.name == "Deft(?) Reroll":
                            print(f"[Renderer] Deft(?) Reroll executed immediately - triggering animation")

                            # Create animation event for immediate execution
                            from boneglaive.graphical.game_state import AnimationEvent
                            anim_event = AnimationEvent(
                                event_type="skill",
                                source_unit=game_unit,
                                target_unit=None,
                                skill_name="DEFT(?) REROLL",
                                skill_target=(game_unit.y, game_unit.x),
                                is_infused=False
                            )

                            # Create skill animation IMMEDIATELY (don't queue it)
                            self._create_skill_animation(anim_event)

                            # Sync state to update visual effects
                            sync_events = self.game_adapter.sync_state()
                            for event in sync_events:
                                if event.event_type != "skill":  # Skip skill events, we already handled it
                                    self.handle_animation_event(event)

                            print(f"[Renderer] Deft(?) Reroll animation triggered")
                    else:
                        print(f"Failed to use skill: {self.selected_skill.name}")

                    # Clear skill targeting mode and hide all ranges
                    self.selected_skill = None
                    self.show_skill_range = False
                    self.skill_positions = []
                    self.show_movement_range = False
                    self.show_target_range = False
                    self.valid_positions = []
                    self.attack_positions = []
                    self.show_skills = False  # Hide skill bar after using a skill
                    self.current_action_mode = "SELECT"
            else:
                print(f"Target out of skill range")
            return  # Don't process normal click logic when in skill mode

        # Unit selection
        if unit:
            # Check if this is a friendly unit (current player's unit)
            if unit.player == current_player:
                # Select friendly unit WITHOUT showing movement range (player must click Move button)
                self.selected_unit = unit
                self.show_movement_range = False
                self.show_target_range = False
                self.current_action_mode = None

                # Query movement range and attack range from game logic (but don't display yet)
                game_unit = self._get_game_unit(unit)
                if game_unit:
                    # If unit has a pending move, clear valid positions
                    if game_unit.move_target:
                        self.valid_positions = []  # No movement range - already moved
                        # Calculate attack range from ghost position by passing from_pos
                        self.attack_positions = self.game_adapter.get_attack_range(game_unit, from_pos=game_unit.move_target)
                    else:
                        # Calculate ranges but don't show them yet
                        self.valid_positions = self.game_adapter.get_movement_range(game_unit)
                        self.attack_positions = self.game_adapter.get_attack_range(game_unit)

                    # Update skill bar, status effects, and unit info
                    self.skill_bar.update(unit, game_unit)
                    self.status_effects_panel.update(game_unit)
                    self.unit_info_panel.update(unit, game_unit)

                    # Check if selected unit is DELPHIC APPRAISER - show astral values
                    from boneglaive.utils.constants import UnitType
                    if game_unit.type == UnitType.DELPHIC_APPRAISER:
                        self.show_astral_values = True
                    else:
                        self.show_astral_values = False
                else:
                    self.valid_positions = []
                    self.attack_positions = []
                    self.skill_bar.update(None, None)
                    self.status_effects_panel.update(None)
                    self.unit_info_panel.update(None, None)
            else:
                # Clicked enemy - attack only if in ATTACK mode
                if self.selected_unit and self.current_action_mode == "ATTACK":
                    # Check if enemy is in attack range
                    if (grid_x, grid_y) in self.attack_positions:
                        game_unit = self._get_game_unit(self.selected_unit)
                        target_unit = self._get_game_unit(unit)

                        if game_unit and target_unit:
                            # Set attack target (game coords: y, x)
                            game_unit.attack_target = (target_unit.y, target_unit.x)
                            game_unit.took_no_actions = False

                            # Track action order
                            game_unit.action_timestamp = self.game_adapter.game.action_counter
                            self.game_adapter.game.action_counter += 1

                            print(f"Attack planned: {self.selected_unit.name} -> {unit.name}")

                            # Clear selection
                            self.selected_unit = None
                            self.show_movement_range = False
                            self.show_target_range = False
                            self.show_skills = False  # Hide skill bar
                            self.show_astral_values = False  # Hide astral values
                            self.valid_positions = []
                            self.attack_positions = []
                            self.skill_bar.update(None, None)
                            self.status_effects_panel.update(None)
                            self.unit_info_panel.update(None, None)
                            self.current_action_mode = "SELECT"
                    else:
                        print(f"Enemy {unit.name} out of attack range")
                elif self.selected_unit and self.current_action_mode != "ATTACK":
                    # Unit selected but not in attack mode - just show enemy info
                    game_unit = self._get_game_unit(unit)
                    if game_unit:
                        self.status_effects_panel.update(game_unit)
                        self.unit_info_panel.update(unit, game_unit)
                else:
                    # Clicked enemy with no unit selected - just show info
                    game_unit = self._get_game_unit(unit)
                    if game_unit:
                        # Update status effects panel and unit info to show enemy info
                        self.status_effects_panel.update(game_unit)
                        self.unit_info_panel.update(unit, game_unit)
                    else:
                        self.status_effects_panel.update(None)
                        self.unit_info_panel.update(None, None)
        else:
            # Clicked tile with no unit
            # Check if it's furniture
            if self.game_adapter.game and self.game_adapter.game.map:
                game_map = self.game_adapter.game.map
                # Convert grid coords to game coords (y, x)
                terrain = game_map.get_terrain_at(grid_y, grid_x)

                if game_map.is_furniture(grid_y, grid_x):
                    # Clicked on furniture - show info
                    furniture_name = self._get_furniture_name(terrain)

                    # Check if player has DELPHIC APPRAISER to see astral value
                    has_appraiser = self._has_delphic_appraiser(current_player)
                    astral_value = None

                    if has_appraiser:
                        # Get astral value (generates if not set)
                        astral_value = game_map.get_cosmic_value(grid_y, grid_x, current_player, self.game_adapter.game)

                    # Create furniture info dict
                    furniture_info = {
                        'name': furniture_name,
                        'position': (grid_x, grid_y),
                        'astral_value': astral_value,
                        'has_appraiser': has_appraiser
                    }

                    # Update unit info panel to show furniture
                    self.unit_info_panel.update_furniture(furniture_info)

                    # Clear other panels
                    self.skill_bar.update(None, None)
                    self.status_effects_panel.update(None)

                    print(f"Selected furniture: {furniture_name} at ({grid_x}, {grid_y})")
                    if astral_value:
                        print(f"  Astral Value: {astral_value}")

                    return  # Don't process as movement

                # Check if it's a Marrow Dike wall tile (attackable obstacle)
                if (self.selected_unit and self.current_action_mode == "ATTACK" and
                    hasattr(self.game_adapter.game, 'marrow_dike_tiles') and
                    (grid_y, grid_x) in self.game_adapter.game.marrow_dike_tiles):

                    # Check if wall is in attack range
                    if (grid_x, grid_y) in self.attack_positions:
                        game_unit = self._get_game_unit(self.selected_unit)

                        if game_unit:
                            # Set attack target on wall (game coords: y, x)
                            game_unit.attack_target = (grid_y, grid_x)
                            game_unit.took_no_actions = False

                            # Track action order
                            game_unit.action_timestamp = self.game_adapter.game.action_counter
                            self.game_adapter.game.action_counter += 1

                            wall_info = self.game_adapter.game.marrow_dike_tiles[(grid_y, grid_x)]
                            print(f"Attack planned: {self.selected_unit.name} -> Marrow Dike wall at ({grid_x}, {grid_y})")

                            # Clear selection
                            self.selected_unit = None
                            self.show_movement_range = False
                            self.show_target_range = False
                            self.show_skills = False
                            self.show_astral_values = False
                            self.valid_positions = []
                            self.attack_positions = []
                            self.skill_bar.update(None, None)
                            self.status_effects_panel.update(None)
                            self.unit_info_panel.update(None, None)
                            self.current_action_mode = "SELECT"
                    else:
                        print(f"Marrow Dike wall at ({grid_x}, {grid_y}) out of attack range")

                    return  # Don't process as movement

            # Not furniture or wall - handle as movement (only in MOVE mode)
            if self.selected_unit and self.current_action_mode == "MOVE":
                # Check if clicked position is in movement range
                if (grid_x, grid_y) in self.valid_positions:
                    # Execute movement
                    game_unit = self._get_game_unit(self.selected_unit)
                    if game_unit:
                        # Check if unit already has a pending move
                        if game_unit.move_target:
                            print(f"{self.selected_unit.name} already has a pending move - cannot move again")
                            return

                        # Set move target (game uses y, x coordinates)
                        game_unit.move_target = (grid_y, grid_x)
                        game_unit.took_no_actions = False

                        # Track action order
                        game_unit.action_timestamp = self.game_adapter.game.action_counter
                        self.game_adapter.game.action_counter += 1

                        print(f"Move planned: {self.selected_unit.name} → ({grid_x}, {grid_y})")

                        # Keep unit selected but update to show attack range from new position
                        # Clear movement range since unit already moved
                        self.show_movement_range = False
                        self.valid_positions = []

                        # Calculate and show attack range from ghost position
                        self.attack_positions = self.game_adapter.get_attack_range(game_unit, from_pos=game_unit.move_target)
                        self.show_target_range = True

                        # Switch to ATTACK mode automatically so user can attack after moving
                        self.current_action_mode = "ATTACK"

                        print(f"  Attack range updated: {len(self.attack_positions)} targets from new position")
                    else:
                        print(f"ERROR: Could not find game unit for {self.selected_unit.name}")
                else:
                    print(f"Cannot move there - not in movement range")
            elif self.selected_unit and self.current_action_mode != "MOVE":
                # Unit selected but not in move mode - inform player
                print(f"Click Move (M) to move the selected unit")

    def _get_unit_id(self, unit) -> Optional[str]:
        """Helper to get unit ID."""
        if not unit:
            return None
        return unit.name  # TODO: Use proper unit ID

    def _handle_action_menu_click(self, action: str):
        """
        Handle action menu button clicks.

        Args:
            action: Action string (move, attack, respawn, execute, concede, help)
        """
        if action == "move":
            if self.selected_unit:
                print("Move mode activated")
                self.current_action_mode = "MOVE"
                self.show_skills = False  # Hide skills when switching to move mode
                # Show movement range
                game_unit = self._get_game_unit(self.selected_unit)
                if game_unit:
                    # Only show movement if unit hasn't moved yet
                    if not game_unit.move_target:
                        self.valid_positions = self.game_adapter.get_movement_range(game_unit)
                        self.show_movement_range = True
                    else:
                        self.valid_positions = []
                        self.show_movement_range = False
                    self.show_target_range = False
                    self.show_skill_range = False

        elif action == "attack":
            if self.selected_unit:
                print("Attack mode activated")
                self.current_action_mode = "ATTACK"
                self.show_skills = False  # Hide skills when switching to attack mode
                # Show attack range
                game_unit = self._get_game_unit(self.selected_unit)
                if game_unit:
                    # If unit has pending move, calculate attack range from ghost position
                    if game_unit.move_target:
                        self.attack_positions = self.game_adapter.get_attack_range(game_unit, from_pos=game_unit.move_target)
                    else:
                        self.attack_positions = self.game_adapter.get_attack_range(game_unit)
                    self.show_target_range = True
                    self.show_movement_range = False
                    self.show_skill_range = False

        elif action == "skills":
            if self.selected_unit:
                print("Skills button clicked - toggling skill bar visibility")
                # Toggle skill bar visibility
                self.show_skills = not self.show_skills
                self.current_action_mode = "SKILLS" if self.show_skills else "SELECT"

        elif action == "respawn":
            print("Respawn mode activated")
            self.start_respawn_mode()

        elif action == "upgrade":
            print("Upgrade mode activated")
            if self.selected_unit:
                game_unit = self._get_game_unit(self.selected_unit)
                if game_unit:
                    success = self.upgrade_window.show(game_unit)
                    if not success:
                        print("No upgrades available for this unit")

        elif action == "help":
            print("Help button clicked")
            # Show help page for selected unit
            if self.selected_unit:
                game_unit = self._get_game_unit(self.selected_unit)
                if game_unit:
                    self.help_page.show(game_unit.type)
                    print(f"Showing help for {game_unit.type}")
            else:
                print("No unit selected for help")

        elif action == "execute":
            print("Executing turn...")
            self.execute_turn()

        elif action == "concede":
            print("Concede requested - showing confirmation dialog")
            self.concede_dialog.show()

    def _get_furniture_name(self, terrain_type) -> str:
        """Convert TerrainType to readable furniture name."""
        # Map terrain types to readable names
        furniture_names = {
            TerrainType.RADIO_CONSOLE: "Radio Console",
            TerrainType.COAT_RACK: "Coat Rack",
            TerrainType.OTTOMAN: "Ottoman",
            TerrainType.CONSOLE: "Console Table",
            TerrainType.CURIOSITY_SHELF: "Curiosity Shelf",
            TerrainType.TIFFANY_LAMP: "Tiffany Lamp",
            TerrainType.EASEL: "Easel",
            TerrainType.SCULPTURE: "Sculpture",
            TerrainType.BENCH: "Bench",
            TerrainType.PODIUM: "Podium",
            TerrainType.VASE: "Vase",
            TerrainType.WORKBENCH: "Workbench",
            TerrainType.COUCH: "Couch",
            TerrainType.TOOLBOX: "Toolbox",
            TerrainType.COT: "Cot",
            TerrainType.CONVEYOR: "Conveyor Belt",
            TerrainType.MINI_PUMPKIN: "Mini Pumpkin",
            TerrainType.POTPOURRI_BOWL: "Potpourri Bowl",
        }
        return furniture_names.get(terrain_type, "Unknown Furniture")

    def _has_delphic_appraiser(self, player: int) -> bool:
        """Check if player has a living DELPHIC APPRAISER unit."""
        if not self.game_adapter.game:
            return False

        from boneglaive.utils.constants import UnitType
        for unit in self.game_adapter.game.units:
            if unit.player == player and unit.type == UnitType.DELPHIC_APPRAISER and unit.hp > 0:
                return True
        return False

    def trigger_screen_shake(self, intensity: float, duration: float):
        """Trigger screen shake effect."""
        self.screen_shake_intensity = intensity
        self.screen_shake_duration = duration

    def trigger_screen_flash(self, color: tuple, duration: float):
        """Trigger screen flash effect with specified color."""
        self.flash_color = color
        self.flash_alpha = 255
        self.flash_duration = duration

    def has_active_animations(self) -> bool:
        """Check if any animations are currently active."""
        # Check for animation objects
        if self.active_animations:
            return True

        # Check if any units are moving
        for unit in self.units:
            if unit.is_moving:
                return True

        # Check for unit-based animations (like VAULT)
        for unit in self.units:
            if hasattr(unit, 'vault_phase') and unit.vault_phase:
                return True
            # Add more animation phase checks here as needed

        return False

    def flush_pending_events(self, only_blocking=False):
        """
        Show all pending damage/heal numbers after animations complete.

        Args:
            only_blocking: If True, only process blocking skill animations and keep
                          non-blocking skills queued for post-execution
        """
        if only_blocking:
            # Filter: process only blocking skills, keep others
            events_to_process = []
            events_to_keep = []

            for event in self.pending_animation_events:
                if event.event_type == "skill":
                    skill_name = event.kwargs.get('skill_name')
                    if skill_name in PRE_EXECUTION_BLOCKING_SKILLS:
                        events_to_process.append(event)
                        print(f"  [Renderer] Processing blocking skill: {skill_name}")
                    else:
                        # Keep non-blocking skills for post-execution
                        events_to_keep.append(event)
                        print(f"  [Renderer] Deferring non-blocking skill for post-execution: {skill_name}")
                else:
                    # Process non-skill events (damage, heal, etc.)
                    events_to_process.append(event)

            for event in events_to_process:
                self._show_event_immediately(event)

            # Keep non-blocking skills in queue
            self.pending_animation_events = events_to_keep
        else:
            # Process all events (normal behavior)
            for event in self.pending_animation_events:
                self._show_event_immediately(event)
            self.pending_animation_events = []

        # After flushing damage/skill events, check all units for active status effects
        # and show icons for any that are currently active
        self._show_active_status_effects()

        # Stop motor animation when all animations complete
        if self.motor_animation.is_running and not self.has_active_animations():
            self.motor_animation.stop()

    def _show_event_immediately(self, event):
        """Show a damage/heal/death/skill event immediately (helper for flushing queue)."""
        if event.event_type == "damage":
            target = event.target_unit
            damage = event.kwargs.get("damage_amount", 0)
            visual_unit = self._get_visual_unit(target)
            if visual_unit:
                animated_unit = visual_unit.animated_unit
                x = animated_unit.x
                y = animated_unit.y - 20
                self.floating_texts.append(FloatingText(x, y, f"-{damage}", COLOR_DAMAGE))
                animated_unit.shake_intensity = 10

        elif event.event_type == "heal":
            target = event.target_unit
            heal = event.kwargs.get("heal_amount", 0)
            visual_unit = self._get_visual_unit(target)
            if visual_unit:
                animated_unit = visual_unit.animated_unit
                x = animated_unit.x
                y = animated_unit.y - 20
                self.floating_texts.append(FloatingText(x, y, f"+{heal}", COLOR_HEAL))
                self.particle_emitter.emit_float(x, y, COLOR_HEAL, count=15)

        elif event.event_type == "geas_heal":
            # Geas break heal animation
            source = event.source_unit  # Unit that had geas
            target = event.target_unit  # Potpourrist healing
            heal = event.kwargs.get("heal_amount", 0)

            print(f"[GeasHeal] Processing geas_heal event: {target.get_display_name() if target else 'None'} heals {heal} HP from {source.get_display_name() if source else 'None'}")

            source_visual = self._get_visual_unit(source)
            target_visual = self._get_visual_unit(target)

            print(f"[GeasHeal] Visual units: source={source_visual is not None}, target={target_visual is not None}")

            if source_visual and target_visual:
                from boneglaive.graphical.animations.potpourrist import GeasBreakHeal

                source_animated = source_visual.animated_unit
                target_animated = target_visual.animated_unit

                print(f"[GeasHeal] Creating animation from ({source_animated.x:.1f}, {source_animated.y:.1f}) to ({target_animated.x:.1f}, {target_animated.y:.1f})")

                # Create geas break heal animation
                animation = GeasBreakHeal(
                    target_x=source_animated.x,
                    target_y=source_animated.y,
                    caster_x=target_animated.x,
                    caster_y=target_animated.y,
                    caster_unit=target_animated,
                    heal_amount=heal
                )
                self.active_animations.append(animation)
                print(f"[GeasHeal] Animation added to active_animations (count: {len(self.active_animations)})")

                # Also show floating heal text
                x = target_animated.x
                y = target_animated.y - 20
                self.floating_texts.append(FloatingText(x, y, f"+{heal}", COLOR_HEAL))

                print(f"[GeasHeal] Animation created successfully!")
            else:
                print(f"[GeasHeal] ERROR: Could not find visual units for animation")

        elif event.event_type == "melange_heal":
            # Melange Eminence passive healing animation
            target = event.target_unit  # POTPOURRIST healing self
            heal = event.kwargs.get("heal_amount", 1)
            infused = event.kwargs.get("infused", False)

            print(f"[MelangeHeal] Processing melange_heal event: {target.get_display_name() if target else 'None'} heals {heal} HP (infused: {infused})")

            target_visual = self._get_visual_unit(target)

            if target_visual:
                target_animated = target_visual.animated_unit

                # Determine which animation class to create directly
                if infused:
                    from boneglaive.graphical.animations.potpourrist import MelangeEminenceInfusedHealAnimation
                    animation_class = MelangeEminenceInfusedHealAnimation
                else:
                    from boneglaive.graphical.animations.potpourrist import MelangeEminenceHealAnimation
                    animation_class = MelangeEminenceHealAnimation

                print(f"[MelangeHeal] Creating {animation_class.__name__} animation at ({target_animated.x:.1f}, {target_animated.y:.1f})")

                # Create animation directly (bypass factory to pass heal_amount)
                animation = animation_class(
                    caster_unit=target_animated,
                    target_unit=target_animated,
                    target_pos=(target.y, target.x),  # grid position (grid_y, grid_x)
                    is_crit=False,
                    is_infused=infused,
                    particle_emitter=self.particle_emitter,
                    debris_list=self.debris_particles,
                    screen_shake_callback=self.trigger_screen_shake,
                    screen_flash_callback=self.trigger_screen_flash,
                    units_list=self.units,
                    camera=self.camera,
                    game=self.game_adapter.game if hasattr(self, 'game_adapter') else None,
                    heal_amount=heal
                )

                if animation:
                    self.active_animations.append(animation)
                    print(f"[MelangeHeal] Animation added to active_animations (count: {len(self.active_animations)})")

                    # Also show floating heal text
                    x = target_animated.x
                    y = target_animated.y - 20
                    self.floating_texts.append(FloatingText(x, y, f"+{heal}", COLOR_HEAL))

                    print(f"[MelangeHeal] Animation created successfully!")
            else:
                print(f"[MelangeHeal] ERROR: Could not find visual unit for animation")

        elif event.event_type == "scalar_trap":
            # Scalar node trap triggered - standing wave explosion
            target = event.target_unit  # Victim who stepped on trap
            trap_pos = event.kwargs.get("trap_position")  # (y, x) in game coords
            damage = event.kwargs.get("damage_amount", 0)

            print(f"[ScalarTrap] Processing scalar_trap event: {target.get_display_name() if target else 'None'} triggers trap at {trap_pos} for {damage} damage")

            target_visual = self._get_visual_unit(target)

            if target_visual and trap_pos:
                from boneglaive.graphical.animations.interferer import ScalarNodeTriggerAnimation

                target_animated = target_visual.animated_unit

                # Convert trap position to screen coordinates
                trap_screen_x = GRID_OFFSET_X + trap_pos[1] * TILE_SIZE + TILE_SIZE // 2
                trap_screen_y = GRID_OFFSET_Y + trap_pos[0] * TILE_SIZE + TILE_SIZE // 2

                print(f"[ScalarTrap] Creating animation at screen coords ({trap_screen_x}, {trap_screen_y})")

                # Create scalar node trigger animation
                animation = ScalarNodeTriggerAnimation(
                    trap_x=trap_screen_x,
                    trap_y=trap_screen_y,
                    target_unit=target_animated,
                    particle_emitter=self.particle_emitter,
                    screen_flash_callback=self.trigger_screen_flash
                )
                self.active_animations.append(animation)
                print(f"[ScalarTrap] Animation added to active_animations (count: {len(self.active_animations)})")

                # Show damage floating text
                x = target_animated.x
                y = target_animated.y - 20
                self.floating_texts.append(FloatingText(x, y, f"-{damage}", COLOR_DAMAGE))
                target_animated.shake_intensity = 12

                print(f"[ScalarTrap] Animation created successfully!")
            else:
                print(f"[ScalarTrap] ERROR: Could not find visual unit or trap position for animation")

        elif event.event_type == "trap_release":
            # Play trap release animation (jaw opening)
            target = event.target_unit  # Unit being released
            visual_unit = self._get_visual_unit(target)
            if visual_unit:
                animated_unit = visual_unit.animated_unit

                # Convert unit position to screen coordinates
                release_x, release_y = self.camera.grid_to_screen(animated_unit.grid_x, animated_unit.grid_y)

                print(f"[TrapRelease] {target.get_display_name()} released from Viseroy trap at grid ({animated_unit.grid_x}, {animated_unit.grid_y}), screen ({release_x}, {release_y})")

                # Create JawRelease animation
                from boneglaive.graphical.animations.mandible_foreman import JawRelease
                jaw_release = JawRelease(release_x, release_y)
                self.active_animations.append(jaw_release)
            else:
                print(f"[TrapRelease] ERROR: Could not find visual unit for released unit")

        elif event.event_type == "viseroy_tick":
            # Trap tick damage - jaws tighten animation
            target = event.target_unit  # Trapped victim taking damage
            damage = event.kwargs.get("damage_amount", 0)
            visual_unit = self._get_visual_unit(target)

            if visual_unit:
                animated_unit = visual_unit.animated_unit

                # Convert unit position to screen coordinates
                tick_x, tick_y = self.camera.grid_to_screen(animated_unit.grid_x, animated_unit.grid_y)

                print(f"[ViseroyTick] {target.get_display_name()} takes {damage} trap tick damage at grid ({animated_unit.grid_x}, {animated_unit.grid_y}), screen ({tick_x}, {tick_y})")

                # Create JawTighten animation
                from boneglaive.graphical.animations.mandible_foreman import JawTighten
                jaw_tighten = JawTighten(tick_x, tick_y)
                self.active_animations.append(jaw_tighten)

                # Show damage floating text
                x = animated_unit.x
                y = animated_unit.y - 20
                self.floating_texts.append(FloatingText(x, y, f"-{damage}", COLOR_DAMAGE))

                # Add screen shake for impact
                animated_unit.shake_intensity = 8

                print(f"[ViseroyTick] JawTighten animation created successfully!")
            else:
                print(f"[ViseroyTick] ERROR: Could not find visual unit for trapped target")

        elif event.event_type == "retch":
            # Unit reached critical health - show retch animation
            target = event.target_unit  # Unit that is retching
            visual_unit = self._get_visual_unit(target)

            if visual_unit:
                animated_unit = visual_unit.animated_unit

                # Use the animated unit's actual screen position (center of sprite)
                # This makes the vomit emanate from the unit itself
                retch_x = animated_unit.x
                retch_y = animated_unit.y

                print(f"[Retch] {target.get_display_name()} retches at critical health at grid ({animated_unit.grid_x}, {animated_unit.grid_y}), screen ({retch_x}, {retch_y})")

                # Create RetchAnimation
                from boneglaive.graphical.animations.core import RetchAnimation
                retch_animation = RetchAnimation(retch_x, retch_y, self.camera)
                self.active_animations.append(retch_animation)

                # Show "RETCH!" floating text in yellow
                x = animated_unit.x
                y = animated_unit.y - 20
                self.floating_texts.append(FloatingText(x, y, "RETCH!", (255, 255, 0)))

                # Add screen shake for critical state
                animated_unit.shake_intensity = 10

                print(f"[Retch] RetchAnimation created successfully!")
            else:
                print(f"[Retch] ERROR: Could not find visual unit for retching unit")

        elif event.event_type == "autoclave_failure":
            # Autoclave failure - GLAIVEMAN charges but fizzles (no targets available)
            target = event.target_unit  # GLAIVEMAN who failed to trigger Autoclave
            visual_unit = self._get_visual_unit(target)

            if visual_unit:
                animated_unit = visual_unit.animated_unit

                print(f"[AutoclaveFailure] {target.get_display_name()}'s Autoclave fails - no targets in range")

                # Create AutoclaveFailureAnimation
                from boneglaive.graphical.animations import AnimationFactory

                failure_animation = AnimationFactory.create_animation(
                    skill_name="AUTOCLAVE_FAILURE",
                    caster_unit=animated_unit,
                    target_unit=animated_unit,
                    target_pos=(target.y, target.x),
                    is_crit=False,
                    is_infused=False,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake,
                    screen_flash_callback=self.trigger_screen_flash,
                    units_list=self.units,
                    camera=self.camera,
                    game=self.game_adapter.game
                )

                if failure_animation:
                    self.active_animations.append(failure_animation)
                    print(f"[AutoclaveFailure] Animation created successfully!")
                else:
                    print(f"[AutoclaveFailure] ERROR: Failed to create animation")
            else:
                print(f"[AutoclaveFailure] ERROR: Could not find visual unit for GLAIVEMAN")

        elif event.event_type == "partition_dissociation":
            # Play partition dissociation animation (emergency trigger)
            print(f"[RENDERER DEBUG] *** RECEIVED partition_dissociation EVENT ***")
            protected_unit = event.target_unit  # Unit that was protected
            derelictionist = event.source_unit  # DERELICTIONIST who cast partition
            print(f"  Protected unit: {protected_unit.get_display_name() if protected_unit else 'None'}")
            print(f"  DERELICTIONIST: {derelictionist.get_display_name() if derelictionist else 'None'}")

            protected_visual = self._get_visual_unit(protected_unit)
            derelictionist_visual = self._get_visual_unit(derelictionist)
            print(f"  Protected visual found: {protected_visual is not None}")
            print(f"  DERELICTIONIST visual found: {derelictionist_visual is not None}")

            if protected_visual and derelictionist_visual:
                print(f"[PartitionDissociation] Creating dissociation animation for {protected_unit.get_display_name()}")

                from boneglaive.graphical.animations import PartitionDissociationAnimation

                dissociation_anim = PartitionDissociationAnimation(
                    protected_unit=protected_visual.animated_unit,
                    derelictionist_unit=derelictionist_visual.animated_unit,
                    camera=self.camera,
                    screen_shake_callback=self.trigger_screen_shake,
                    screen_flash_callback=self.trigger_screen_flash,
                    particle_emitter=self.particle_emitter
                )

                self.active_animations.append(dissociation_anim)
                print(f"[PartitionDissociation] Dissociation animation CREATED and added to active_animations (count: {len(self.active_animations)})")
            else:
                if not protected_visual:
                    print(f"[PartitionDissociation] ERROR: Could not find visual unit for protected unit {protected_unit.get_display_name()}")
                if not derelictionist_visual:
                    print(f"[PartitionDissociation] ERROR: Could not find visual unit for DERELICTIONIST {derelictionist.get_display_name()}")

        elif event.event_type == "teleport_defection":
            # Play DERELICTIONIST defection teleport animation
            print(f"[RENDERER DEBUG] *** RECEIVED teleport_defection EVENT ***")
            derelictionist = event.source_unit
            origin_pos = event.kwargs.get("origin_pos")  # (y, x) in game coords
            destination_pos = event.kwargs.get("destination_pos")  # (y, x) in game coords
            print(f"  DERELICTIONIST: {derelictionist.get_display_name() if derelictionist else 'None'}")
            print(f"  Origin: {origin_pos}, Destination: {destination_pos}")

            derelictionist_visual = self._get_visual_unit(derelictionist)
            print(f"  DERELICTIONIST visual found: {derelictionist_visual is not None}")

            if derelictionist_visual and origin_pos and destination_pos:
                print(f"[DefectTeleport] Creating defection teleport animation for {derelictionist.get_display_name()}")

                from boneglaive.graphical.animations.derelictionist import DerelictionistDefectTeleportAnimation

                teleport_anim = DerelictionistDefectTeleportAnimation(
                    derelictionist_unit=derelictionist_visual.animated_unit,
                    origin_pos=origin_pos,
                    destination_pos=destination_pos,
                    camera=self.camera,
                    screen_shake_callback=self.trigger_screen_shake,
                    particle_emitter=self.particle_emitter
                )

                self.active_animations.append(teleport_anim)
                print(f"[DefectTeleport] Teleport animation CREATED and added to active_animations (count: {len(self.active_animations)})")
            else:
                if not derelictionist_visual:
                    print(f"[DefectTeleport] ERROR: Could not find visual unit for DERELICTIONIST {derelictionist.get_display_name()}")
                if not origin_pos:
                    print(f"[DefectTeleport] ERROR: No origin position provided")
                if not destination_pos:
                    print(f"[DefectTeleport] ERROR: No destination position provided")

        elif event.event_type == "death":
            # Play death animation - blood explosion
            unit = event.source_unit
            visual_unit = self._get_visual_unit(unit)
            if visual_unit:
                animated_unit = visual_unit.animated_unit
                # Create blood explosion
                self.particle_emitter.emit_blood_explosion(
                    animated_unit.x,
                    animated_unit.y,
                    count=80
                )
                # Screen shake for impact
                self.trigger_screen_shake(8, 0.3)
                print(f"[Death] {unit.get_display_name()} death animation triggered (blood explosion)")

        elif event.event_type == "attack":
            # Create basic attack animation from queued event
            self._create_attack_animation(event)

        elif event.event_type == "skill":
            # Create skill animation from queued event
            self._create_skill_animation(event)

        elif event.event_type == "glaive_sweep":
            # Create Glaive Sweep counter-attack animation
            self._create_glaive_sweep_animation(event)

    def _update_animations_only(self, delta_time: float):
        """
        Update only animations and visual effects (no game state sync).
        Used for blocking pre-execution animations.

        Args:
            delta_time: Time since last frame in seconds
        """
        # Update screen shake
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= delta_time
            if self.screen_shake_duration <= 0:
                self.screen_shake_intensity = 0

        # Update screen flash
        if self.flash_duration > 0:
            self.flash_duration -= delta_time
            self.flash_alpha = int(255 * max(0, self.flash_duration / 0.2))

        # Update units (for smooth visual movement)
        for unit in self.units:
            unit.update(delta_time)

        # Update particles
        updated_particles = []
        for particle in self.particle_emitter.particles:
            if particle.update(delta_time):
                updated_particles.append(particle)
        self.particle_emitter.particles = updated_particles

        # Update debris particles
        updated_debris = []
        for debris in self.debris_particles:
            if debris.update(delta_time):
                updated_debris.append(debris)
        self.debris_particles = updated_debris

        # Update active animations
        updated_animations = []
        for anim in self.active_animations:
            still_active = anim.update(delta_time)
            if still_active:
                updated_animations.append(anim)
        self.active_animations = updated_animations

        # Update background animations (non-blocking persistent effects like zones)
        updated_background = []
        for anim in self.background_animations:
            still_active = anim.update(delta_time)
            if still_active:
                updated_background.append(anim)
        self.background_animations = updated_background

        # Update motor animation
        self.motor_animation.update(delta_time)

        # Update floating texts
        updated_texts = []
        for text in self.floating_texts:
            still_active = text.update(delta_time)
            if still_active:
                updated_texts.append(text)
        self.floating_texts = updated_texts

    def update(self, delta_time: float):
        """
        Update game state and animations.

        Args:
            delta_time: Time since last frame in seconds
        """
        if self.paused:
            return

        # Skip game state updates if game is over (but continue visual updates)
        if self.game_over_window.visible:
            # Still update visual effects for polish
            self.screen_shake_duration = max(0, self.screen_shake_duration - delta_time)
            if self.screen_shake_duration <= 0:
                self.screen_shake_intensity = 0

            self.flash_duration = max(0, self.flash_duration - delta_time)
            self.flash_alpha = int(255 * max(0, self.flash_duration / 0.2))

            # Update animations so they finish playing
            for unit in self.units:
                unit.update(delta_time)
            self.particle_emitter.update(delta_time)
            self.floating_texts = [t for t in self.floating_texts if t.update(delta_time)]

            updated_animations = []
            for anim in self.active_animations:
                if anim.update(delta_time):
                    updated_animations.append(anim)
            self.active_animations = updated_animations

            return

        # Check if we need to enter setup mode
        if (self.game_adapter.game and
            self.game_adapter.game.setup_phase and
            not self.setup_mode):
            self.start_setup_mode()

        # Update astral value pulse animation
        self.astral_value_pulse_time += delta_time

        # Update Rail Genesis junction pulse animation
        self.junction_pulse_time += delta_time

        # Update imbued furniture sparkles
        updated_sparkles = []
        for sparkle in self.imbued_sparkles:
            # Age the sparkle
            sparkle['life'] += delta_time

            # Remove if too old
            if sparkle['life'] >= sparkle['max_life']:
                continue

            # Update position
            sparkle['x'] += sparkle['vx'] * delta_time
            sparkle['y'] += sparkle['vy'] * delta_time

            updated_sparkles.append(sparkle)

        self.imbued_sparkles = updated_sparkles

        # Update screen shake
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= delta_time
            if self.screen_shake_duration <= 0:
                self.screen_shake_intensity = 0

        # Update flash
        if self.flash_duration > 0:
            self.flash_duration -= delta_time
            self.flash_alpha = int(255 * max(0, self.flash_duration / 0.2))

        # Sync with game state
        # PERFORMANCE FIX: Don't call sync_state every frame - it's 534 lines of checks!
        # Only sync when something actually happened that could change game state:
        # - After execute_turn() (already handled in execute_turn method)
        # - When animations are playing (state might be changing)
        # - When explicitly requested via _force_sync flag
        #
        # During idle frames (setup phase, waiting for input), skip sync entirely
        should_sync = (
            len(self.active_animations) > 0 or  # Animations playing
            hasattr(self, '_force_sync') and self._force_sync  # Forced sync flag
        )

        if should_sync:
            animation_events = self.game_adapter.sync_state()
            for event in animation_events:
                self.handle_animation_event(event)
            if hasattr(self, '_force_sync'):
                self._force_sync = False

        # Update units
        for unit in self.units:
            unit.update(delta_time)

        # Update particles
        self.particle_emitter.update(delta_time)
        self.floating_texts = [t for t in self.floating_texts if t.update(delta_time)]

        # Sync combat log with game's message log
        if self.game_adapter.game:
            self.combat_log.add_messages_from_game_log(message_log, count=20)

        # Check for game over condition - but wait for all animations to finish first
        if (self.game_adapter.game and
            self.game_adapter.game.winner and
            not self.game_over_window.visible and
            not self.has_active_animations() and
            not self.pending_animation_events):
            self.show_game_over_window()

        # Update debris with collision detection (for PRY splash damage)
        if len(self.debris_particles) > 0 and not hasattr(self, '_debris_logged'):
            print(f"[Renderer] Updating {len(self.debris_particles)} debris particles")
            print(f"  debris_particles list: id={id(self.debris_particles)}")
            if self.debris_particles:
                d = self.debris_particles[0]
                print(f"  First debris: pos=({d.x:.1f}, {d.y:.1f}), vel=({d.vx:.1f}, {d.vy:.1f}), lifetime={d.lifetime:.2f}")
            self._debris_logged = True
        remaining_debris = []
        debris_collision_count = 0
        debris_removed_count = 0
        for debris in self.debris_particles:
            still_alive = debris.update(delta_time)
            if still_alive:
                # Check collision with target unit
                collision = debris.check_collision(self.units, self.particle_emitter)
                if collision:
                    debris_collision_count += 1
                    # check_collision already creates particle burst and sets lifetime=0
                else:
                    remaining_debris.append(debris)
            else:
                debris_removed_count += 1
        if debris_collision_count > 0 or debris_removed_count > 0:
            print(f"[Debris] Collisions: {debris_collision_count}, Removed (lifetime): {debris_removed_count}, Remaining: {len(remaining_debris)}")
        self.debris_particles = remaining_debris

        # Update active animations and check for impact effects
        updated_animations = []
        for anim in self.active_animations:
            still_active = anim.update(delta_time)

            # Check if animation triggered an impact effect
            if hasattr(anim, 'trigger_impact') and anim.trigger_impact:
                # Create impact effects at animation's target position
                self.particle_emitter.emit_burst(anim.target_x, anim.target_y, (255, 215, 0), count=40)

                # Additional sparkle particles
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(100, 250)
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    particle = Particle(anim.target_x, anim.target_y, vx, vy,
                                      (255, 255, 200), random.uniform(3, 6), 0.5)
                    self.particle_emitter.particles.append(particle)

                # Check if this is a critical hit (Judgement)
                is_critical = hasattr(anim, 'is_crit') and anim.is_crit

                if is_critical:
                    # DIVINE LIGHTNING STRIKE!
                    lightning = LightningBolt(anim.target_x, anim.target_y)
                    self.active_animations.append(lightning)

                    # Golden/white screen flash
                    self.flash_color = (255, 255, 255)
                    self.flash_alpha = 255
                    self.flash_duration = 0.2

                    # "DIVINE JUDGMENT!" floating text
                    judgment_text = FloatingText(anim.target_x, anim.target_y - 40,
                                                "DIVINE JUDGMENT!", (255, 215, 0))
                    self.floating_texts.append(judgment_text)

                    # Extra screen shake for critical
                    self.screen_shake_intensity = 15
                    self.screen_shake_duration = 0.5

                    # Extra electric particles
                    for _ in range(30):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(150, 300)
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed
                        particle = Particle(anim.target_x, anim.target_y, vx, vy,
                                          (200, 220, 255), random.uniform(2, 5), 0.4)
                        self.particle_emitter.particles.append(particle)
                else:
                    # Normal hit - regular debris and shake
                    for _ in range(10):
                        vx = random.uniform(-150, 150)
                        vy = random.uniform(-200, -50)
                        size = random.randint(3, 8)
                        debris = DebrisParticle(anim.target_x, anim.target_y, vx, vy, size, color=(200, 200, 200))
                        self.debris_particles.append(debris)

                    self.screen_shake_intensity = 8
                    self.screen_shake_duration = 0.3

                anim.trigger_impact = False  # Reset flag

            # Check if ExpediteRush animation just completed - trigger JawClamp on enemy
            if hasattr(anim, 'foreman') and anim.foreman and not still_active:
                # Animation completed, check if foreman hit an enemy during Expedite
                # Find the game unit at the foreman's position using game.get_unit_at
                foreman_grid_x = anim.foreman.grid_x
                foreman_grid_y = anim.foreman.grid_y

                # Look up the game unit at this position
                game_unit = None
                if self.game_adapter.game:
                    game_unit = self.game_adapter.game.get_unit_at(foreman_grid_y, foreman_grid_x)

                if game_unit and hasattr(game_unit, 'expedite_enemy_hit') and game_unit.expedite_enemy_hit:
                    from boneglaive.graphical.animations.mandible_foreman import JawClamp

                    enemy = game_unit.expedite_enemy_hit
                    enemy_pos = game_unit.expedite_enemy_pos  # (y, x) format

                    # Convert enemy position to screen coordinates
                    jaw_x, jaw_y = self.camera.grid_to_screen(enemy_pos[1], enemy_pos[0])  # (x, y) = (col, row)

                    print(f"  [Renderer] ExpediteRush hit enemy at grid ({enemy_pos[1]}, {enemy_pos[0]})")
                    print(f"  [Renderer] Creating JawClamp animation at enemy screen position ({jaw_x}, {jaw_y})")

                    jaw_animation = JawClamp(jaw_x, jaw_y)
                    if jaw_animation:
                        self.active_animations.append(jaw_animation)
                        print(f"  [Animation] Successfully triggered JawClamp animation on Expedite enemy hit")
                    else:
                        print(f"  [Animation] WARNING: Failed to create JawClamp animation")

                    # Clear the expedite enemy hit flag
                    game_unit.expedite_enemy_hit = None
                    game_unit.expedite_enemy_pos = None

            if still_active:
                updated_animations.append(anim)

        self.active_animations = updated_animations

        # Update background animations (non-blocking persistent effects like zones)
        updated_background = []
        for anim in self.background_animations:
            still_active = anim.update(delta_time)
            if still_active:
                updated_background.append(anim)
        self.background_animations = updated_background

        # Update motor animation
        self.motor_animation.update(delta_time)

        # Check if all animations finished - if so, flush pending damage/heal/death events
        if self.pending_animation_events and not self.has_active_animations():
            self.flush_pending_events()
        elif not self.has_active_animations() and hasattr(self.game_adapter, '_effects_to_show_after_damage') and self.game_adapter._effects_to_show_after_damage:
            # No pending damage events, but we have status icons to show
            print(f"[Renderer] No pending events, but showing {len(self.game_adapter._effects_to_show_after_damage)} status effect icons")
            self._show_active_status_effects()
            # Note: List is cleared inside _show_active_status_effects() to prevent duplicates

        # Stop motor if it's running and turn execution is complete (no more animations)
        if self.motor_animation.is_running and not self.has_active_animations() and not self.game_adapter.executing_turn:
            self.motor_animation.stop()

        # After all animations complete (including status icons from flush), clean up dead units
        # This ensures death animations have access to visual_units before removal
        if not self.pending_animation_events and not self.has_active_animations():
            self.sync_units_from_game()

    def handle_animation_event(self, event: AnimationEvent):
        """
        Create and queue visual animations based on game events.

        Args:
            event: Animation event from game state
        """
        if event.event_type == "damage" or event.event_type == "heal" or event.event_type == "geas_heal" or event.event_type == "melange_heal" or event.event_type == "scalar_trap" or event.event_type == "trap_release" or event.event_type == "viseroy_tick" or event.event_type == "retch" or event.event_type == "autoclave_failure":
            # If animations are active, queue the event for later
            if self.has_active_animations():
                self.pending_animation_events.append(event)
                return

            # Otherwise show immediately
            self._show_event_immediately(event)

        elif event.event_type == "death":
            # IMPORTANT: Death should happen AFTER killing blow animation completes
            # Queue death event if animations are active
            if self.has_active_animations():
                self.pending_animation_events.append(event)
                return

            # Otherwise show death immediately
            self._show_event_immediately(event)

        elif event.event_type == "attack":
            # ALWAYS queue basic attack animations during turn execution
            # This ensures attacks trigger AFTER units reach their destination
            self.pending_animation_events.append(event)
            print(f"  [Renderer] Queued basic attack animation")

        elif event.event_type == "skill":
            # ALWAYS queue skill animations during turn execution
            # This ensures skills trigger AFTER units reach their destination
            # Movement events are processed in the same sync_state() call,
            # so we need to queue skills and let them flush after movement completes
            self.pending_animation_events.append(event)
            print(f"  [Renderer] Queued skill animation: {event.kwargs.get('skill_name')}")

        elif event.event_type == "glaive_sweep":
            # ALWAYS queue glaive sweep animations during turn execution
            # This is the upgraded Autoclave counter-attack
            self.pending_animation_events.append(event)
            print(f"  [Renderer] Queued Glaive Sweep counter-attack animation")

        elif event.event_type == "status_effect":
            # NOTE: Status effect events are NO LONGER handled here to prevent duplicate flashes.
            # All status effects (including trap-applied ones like shrapnel) are now detected
            # via _detect_status_effects_callback() and shown via _show_active_status_effects().
            # This ensures each effect flashes exactly ONCE after damage numbers complete.
            print(f"  [Renderer] Ignoring status_effect event (will be detected via callback system)")

        elif event.event_type == "partition_dissociation":
            # Partition dissociation is a dramatic emergency animation - show immediately
            # This takes priority and should not be queued
            self._show_event_immediately(event)
            print(f"  [Renderer] Triggered partition dissociation animation immediately")

        elif event.event_type == "zone_create":
            # Zone creation (e.g., Selenic Backdraft from upgraded Demilune)
            # Create persistent zone animation immediately - NON-BLOCKING
            # Zone should appear and persist independently of skill animations
            zone_name = event.kwargs.get('zone_name')
            zone_tiles = event.kwargs.get('zone_tiles', [])

            print(f"  [Renderer] Received zone_create event: zone_name={zone_name}, tiles={zone_tiles}")

            if zone_name and zone_tiles:
                print(f"  [Renderer] Creating {zone_name} zone animation IMMEDIATELY on {len(zone_tiles)} tiles")

                # Find animated unit for caster
                caster_animated = self._find_animated_unit_by_game_unit(event.source_unit)

                if caster_animated:
                    # Create zone animation via AnimationFactory
                    from boneglaive.graphical.animations import AnimationFactory

                    zone_animation = AnimationFactory.create_animation(
                        skill_name=zone_name,
                        caster_unit=caster_animated,
                        target_unit=None,
                        target_pos=None,
                        is_crit=False,
                        is_infused=False,
                        particle_emitter=self.particle_emitter,
                        screen_shake_callback=self.trigger_screen_shake,
                        screen_flash_callback=self.trigger_screen_flash,
                        units_list=self.units,
                        camera=self.camera,
                        game=self.game_adapter.game,
                        zone_tiles=zone_tiles  # Pass zone tiles as kwarg
                    )

                    if zone_animation:
                        # Add to background_animations - non-blocking, persistent effect
                        # Background animations don't block pending_animation_events from flushing
                        self.background_animations.append(zone_animation)
                        print(f"  [Animation] Successfully created {zone_name} zone in BACKGROUND (non-blocking)")
                    else:
                        print(f"  [Animation] WARNING: Failed to create {zone_name} zone animation")
                else:
                    print(f"  [Renderer] WARNING: Could not find animated unit for zone caster")

            # DON'T BLOCK - zone is independent background effect

        elif event.event_type == "building_create":
            # Building creation (e.g., Derelict buildings from upgraded Derelict)
            # Create building formation animation (one-time) and persistent building tiles (background)
            building_tiles = event.kwargs.get('building_tiles', [])

            print(f"  [Renderer] Received building_create event: {len(building_tiles)} tiles")

            if building_tiles:
                print(f"  [Renderer] Creating Derelict building animations on {len(building_tiles)} tiles")

                # Find animated unit for caster
                caster_animated = self._find_animated_unit_by_game_unit(event.source_unit)

                if caster_animated:
                    # Create building formation animation via AnimationFactory
                    from boneglaive.graphical.animations import AnimationFactory

                    # 1. Building formation animation (one-time, blocking)
                    formation_animation = AnimationFactory.create_animation(
                        skill_name="DERELICT_BUILDING_FORMATION",
                        caster_unit=caster_animated,
                        target_unit=None,
                        target_pos=None,
                        is_crit=False,
                        is_infused=False,
                        particle_emitter=self.particle_emitter,
                        screen_shake_callback=self.trigger_screen_shake,
                        screen_flash_callback=self.trigger_screen_flash,
                        units_list=self.units,
                        camera=self.camera,
                        game=self.game_adapter.game,
                        building_tiles=building_tiles
                    )

                    if formation_animation:
                        # Add to active_animations - this is a one-time formation effect
                        self.active_animations.append(formation_animation)
                        print(f"  [Animation] Successfully created building formation animation")
                    else:
                        print(f"  [Animation] WARNING: Failed to create building formation animation")

                    # 2. Building tiles persistent effect (background, non-blocking)
                    tiles_animation = AnimationFactory.create_animation(
                        skill_name="DERELICT_BUILDING_TILES",
                        caster_unit=caster_animated,
                        target_unit=None,
                        target_pos=None,
                        is_crit=False,
                        is_infused=False,
                        particle_emitter=self.particle_emitter,
                        screen_shake_callback=self.trigger_screen_shake,
                        screen_flash_callback=self.trigger_screen_flash,
                        units_list=self.units,
                        camera=self.camera,
                        game=self.game_adapter.game,
                        building_tiles=building_tiles
                    )

                    if tiles_animation:
                        # Add to background_animations - non-blocking, persistent effect
                        self.background_animations.append(tiles_animation)
                        print(f"  [Animation] Successfully created building tiles in BACKGROUND (non-blocking)")
                    else:
                        print(f"  [Animation] WARNING: Failed to create building tiles animation")
                else:
                    print(f"  [Renderer] WARNING: Could not find animated unit for building caster")

            # Building formation is blocking, but tiles are background effect

        elif event.event_type == "movement":
            # Animate unit movement - already handled in sync_state()
            # The AnimatedUnit.move_to_grid() is called automatically
            pass

    def _create_status_icon_flash(self, animated_unit, effect_name):
        """
        Create and queue a status icon flash animation.

        Args:
            animated_unit: AnimatedUnit to flash icon on
            effect_name: Name of the status effect
        """
        from boneglaive.graphical.animations.core import StatusIconFlash

        # Special handling for derelicted status - play full animation in addition to icon flash
        if effect_name == 'derelicted':
            from boneglaive.graphical.animations.derelictionist import DerelictedApplicationAnimation

            print(f"  [Renderer] Creating Derelicted application animation (in addition to icon flash)...")
            animation = DerelictedApplicationAnimation(
                target_unit=animated_unit,
                camera=self.camera,
                screen_shake_callback=self.trigger_screen_shake,
                screen_flash_callback=self.trigger_screen_flash,
                particle_emitter=self.particle_emitter
            )
            if animation:
                self.active_animations.append(animation)
                print(f"  [Animation] Successfully triggered Derelicted application animation")
            else:
                print(f"  [Animation] WARNING: Failed to create Derelicted application animation")
            # Continue to also create the icon flash below

        # Regular status icon flash for all effects (including derelicted)
        print(f"  [Renderer] Creating status icon flash for {effect_name}...")
        animation = StatusIconFlash(animated_unit, effect_name)
        if animation:
            self.active_animations.append(animation)
            print(f"  [Animation] Successfully triggered status icon flash: {effect_name}")
        else:
            print(f"  [Animation] WARNING: Failed to create status icon flash")

    def _show_active_status_effects(self):
        """
        Show status effect icons for effects that were detected during turn execution.
        Called after damage numbers are flushed.
        IMPORTANT: Clears the effects list after showing to prevent duplicate flashes.
        """
        if not self.game_adapter.game:
            return

        # Check if we have effects stored from the callback
        if not hasattr(self.game_adapter, '_effects_to_show_after_damage'):
            print("[Renderer] No effects to show (no _effects_to_show_after_damage attribute)")
            return

        effects_list = self.game_adapter._effects_to_show_after_damage
        if not effects_list:
            print("[Renderer] No effects to show (empty list)")
            return

        print(f"[Renderer] Showing {len(effects_list)} status effect icons...")

        for unit_id, effect_name in effects_list:
            if unit_id in self.game_adapter.visual_units:
                visual_unit = self.game_adapter.visual_units[unit_id]
                animated_unit = visual_unit.animated_unit
                game_unit = visual_unit.game_unit
                print(f"[Renderer] Showing {effect_name} icon for {game_unit.get_display_name()}")
                self._create_status_icon_flash(animated_unit, effect_name)
            else:
                print(f"[Renderer] WARNING: Unit {unit_id} not found in visual_units")

        # Clear the list immediately after showing to prevent duplicate flashes
        self.game_adapter._effects_to_show_after_damage.clear()
        print(f"[Renderer] Cleared effects list to prevent duplicates")

    def _create_attack_animation(self, event):
        """
        Create and queue a basic attack animation from an event.
        Helper method used by both handle_animation_event() and _show_event_immediately().

        Args:
            event: AnimationEvent with type "attack"
        """
        from boneglaive.graphical.animations.core import BasicMeleeAttackAnimation

        attacker = event.source_unit
        attack_target = event.kwargs.get("attack_target")  # (y, x) in game coords

        print(f"  [Renderer] Processing basic attack event: {attacker.get_display_name() if attacker else 'None'} → {attack_target}")

        # Find attacker visual unit
        attacker_animated = self._get_visual_unit(attacker)
        if attacker_animated:
            attacker_animated = attacker_animated.animated_unit
            print(f"  [Renderer] Found attacker visual unit at ({attacker_animated.grid_x}, {attacker_animated.grid_y})")
        else:
            print(f"  [Renderer] WARNING: Could not find visual unit for attacker!")
            return

        # Find target unit if any
        target_unit = None
        if attack_target:
            target_grid_x = attack_target[1]  # Convert (y,x) to (x,y)
            target_grid_y = attack_target[0]
            target_unit = self._get_unit_at_grid(target_grid_x, target_grid_y)
            if not target_unit:
                print(f"  [Renderer] WARNING: Could not find target unit at {attack_target}")
                # Continue anyway - animation will work without target

        # Create animation
        print(f"  [Renderer] Creating basic melee attack animation...")
        animation = BasicMeleeAttackAnimation(
            attacker_unit=attacker_animated,
            target_unit=target_unit,
            particle_emitter=self.particle_emitter,
            screen_shake_callback=self.trigger_screen_shake
        )
        if animation:
            self.active_animations.append(animation)
            print(f"  [Animation] Successfully triggered basic attack animation")
        else:
            print(f"  [Animation] WARNING: Failed to create basic attack animation")

        # Check if attacker is INTERFERER and trigger Neutron Illuminant passive flash
        print(f"  [DEBUG] Checking for INTERFERER: attacker={attacker}, has type={hasattr(attacker, 'type') if attacker else False}")
        if attacker and hasattr(attacker, 'type') and attacker.type:
            from boneglaive.utils.constants import UnitType
            # Handle DLC units (integer enum values)
            if hasattr(attacker.type, 'name'):
                unit_type_name = attacker.type.name
            else:
                unit_type_name = str(attacker.type)
            print(f"  [DEBUG] Attacker unit type: {unit_type_name}")
            if attacker.type == UnitType.INTERFERER and attack_target:
                print(f"  [Renderer] *** INTERFERER ATTACK DETECTED ***")

                # Check if this attack has carrier_rave flag (captured from game state BEFORE execution cleared it)
                has_carrier_rave = event.kwargs.get("has_carrier_rave", False)
                use_basic_attack = not has_carrier_rave  # Use dual carabiner swing for basic attacks

                if has_carrier_rave:
                    print(f"  [Renderer] *** CARRIER RAVE FLAG DETECTED - using triple strike animation ***")

                from boneglaive.graphical.animations.animation_factory import AnimationFactory

                if use_basic_attack and target_unit:
                    # Use dual carabiner swing for basic attacks with Neutron Illuminant flash
                    print(f"  [Renderer] Using dual carabiner swing for basic attack with flash")
                    from boneglaive.graphical.animations.interferer import InterfererDualCarabinerAttack

                    carabiner_attack = InterfererDualCarabinerAttack(
                        attacker_unit=attacker_animated,
                        target_unit=target_unit,
                        particle_emitter=self.particle_emitter,
                        screen_shake_callback=self.trigger_screen_shake,
                        screen_flash_callback=self.trigger_screen_flash
                    )
                    if carabiner_attack:
                        self.active_animations.append(carabiner_attack)
                        print(f"  [Animation] Successfully triggered INTERFERER dual carabiner swing with flash")
                    else:
                        print(f"  [Animation] WARNING: Failed to create INTERFERER carabiner attack")

                elif has_carrier_rave:
                    # Use triple strike animation
                    print(f"  [Renderer] Creating KARRIER_RAVE_STRIKE animation (triple strike)")

                    # Convert target to screen coords
                    target_grid_x = attack_target[1]
                    target_grid_y = attack_target[0]
                    target_visual_unit = self._get_unit_at_grid(target_grid_x, target_grid_y)

                    karrier_animation = AnimationFactory.create_animation(
                        skill_name="KARRIER_RAVE_STRIKE",
                        caster_unit=attacker_animated,
                        target_unit=target_visual_unit,
                        target_pos=(target_grid_y, target_grid_x),
                        particle_emitter=self.particle_emitter,
                        screen_flash_callback=self.trigger_screen_flash,
                        camera=self.camera
                    )

                    if karrier_animation:
                        self.active_animations.append(karrier_animation)
                        print(f"  [Animation] *** Successfully triggered KARRIER RAVE triple strike - added to active_animations (count: {len(self.active_animations)}) ***")
                    else:
                        print(f"  [Animation] WARNING: Failed to create KARRIER RAVE strike animation")
                else:
                    # Use normal Neutron Illuminant flash animation
                    # Determine attack direction (cardinal vs diagonal)
                    attacker_y, attacker_x = attacker.y, attacker.x
                    target_y, target_x = attack_target[0], attack_target[1]
                    dy = target_y - attacker_y
                    dx = target_x - attacker_x

                    # Normalize direction
                    is_cardinal = (dy == 0 or dx == 0)

                    skill_name = "NEUTRON_ILLUMINANT_CARDINAL" if is_cardinal else "NEUTRON_ILLUMINANT_DIAGONAL"
                    print(f"  [Renderer] Creating {skill_name} flash (direction: dy={dy}, dx={dx}, is_cardinal={is_cardinal})")

                    neutron_animation = AnimationFactory.create_animation(
                        skill_name=skill_name,
                        caster_unit=attacker_animated,
                        target_unit=None,
                        target_pos=None,
                        particle_emitter=self.particle_emitter,
                        screen_flash_callback=self.trigger_screen_flash,
                        camera=self.camera
                    )

                    if neutron_animation:
                        self.active_animations.append(neutron_animation)
                        print(f"  [Animation] *** Successfully triggered Neutron Illuminant flash - added to active_animations (count: {len(self.active_animations)}) ***")
                    else:
                        print(f"  [Animation] WARNING: Failed to create Neutron Illuminant animation")

            # Check if attacker is MANDIBLE_FOREMAN and trigger JawClamp animation on hit
            elif attacker.type == UnitType.MANDIBLE_FOREMAN and attack_target and target_unit:
                print(f"  [Renderer] *** MANDIBLE_FOREMAN ATTACK DETECTED ***")
                from boneglaive.graphical.animations.mandible_foreman import JawClamp

                # Convert target position to screen coordinates
                target_x, target_y = self.camera.grid_to_screen(target_unit.grid_x, target_unit.grid_y)

                print(f"  [Renderer] Creating JawClamp animation at target position ({target_x}, {target_y})")
                jaw_animation = JawClamp(target_x, target_y)
                if jaw_animation:
                    self.active_animations.append(jaw_animation)
                    print(f"  [Animation] Successfully triggered JawClamp animation on MANDIBLE_FOREMAN hit")
                else:
                    print(f"  [Animation] WARNING: Failed to create JawClamp animation")

            # Check if attacker is GLAIVEMAN and trigger polearm sweep animation
            elif attacker.type == UnitType.GLAIVEMAN and attack_target and target_unit:
                print(f"  [Renderer] *** GLAIVEMAN ATTACK DETECTED ***")
                from boneglaive.graphical.animations.glaiveman import GlaivemanPolearmAttack

                polearm_animation = GlaivemanPolearmAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if polearm_animation:
                    self.active_animations.append(polearm_animation)
                    print(f"  [Animation] Successfully triggered GLAIVEMAN polearm sweep animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create GLAIVEMAN polearm animation")

            # Check if attacker is GRAYMAN and trigger psychic attack animation
            elif attacker.type == UnitType.GRAYMAN and attack_target and target_unit:
                print(f"  [Renderer] *** GRAYMAN ATTACK DETECTED ***")
                from boneglaive.graphical.animations.grayman import GraymanPsychicAttack

                psychic_animation = GraymanPsychicAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if psychic_animation:
                    self.active_animations.append(psychic_animation)
                    print(f"  [Animation] Successfully triggered GRAYMAN psychic attack animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create GRAYMAN psychic animation")

            # Check if attacker is MARROW_CONDENSER and trigger bone ball attack animation
            elif attacker.type == UnitType.MARROW_CONDENSER and attack_target and target_unit:
                print(f"  [Renderer] *** MARROW_CONDENSER ATTACK DETECTED ***")
                from boneglaive.graphical.animations.marrow_condenser import MarrowCondenserBoneAttack

                bone_attack = MarrowCondenserBoneAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if bone_attack:
                    self.active_animations.append(bone_attack)
                    print(f"  [Animation] Successfully triggered MARROW_CONDENSER bone ball attack animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create MARROW_CONDENSER bone attack")

            # Check if attacker is FOWL_CONTRIVANCE and trigger electromagnetic bolt attack animation
            elif attacker.type == UnitType.FOWL_CONTRIVANCE and attack_target and target_unit:
                print(f"  [Renderer] *** FOWL_CONTRIVANCE ATTACK DETECTED ***")
                from boneglaive.graphical.animations.fowl_contrivance import FowlContrivanceElectromagneticAttack

                em_attack = FowlContrivanceElectromagneticAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if em_attack:
                    self.active_animations.append(em_attack)
                    print(f"  [Animation] Successfully triggered FOWL_CONTRIVANCE electromagnetic bolt animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create FOWL_CONTRIVANCE EM attack")

            # Check if attacker is DELPHIC_APPRAISER and trigger astral appraisal attack animation
            elif attacker.type == UnitType.DELPHIC_APPRAISER and attack_target and target_unit:
                print(f"  [Renderer] *** DELPHIC_APPRAISER ATTACK DETECTED ***")
                from boneglaive.graphical.animations.delphic_appraiser import DelphicAppraiserAstralAttack

                astral_attack = DelphicAppraiserAstralAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if astral_attack:
                    self.active_animations.append(astral_attack)
                    print(f"  [Animation] Successfully triggered DELPHIC_APPRAISER astral attack animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create DELPHIC_APPRAISER astral attack")

            # Check if attacker is GAS_MACHINIST and trigger pressurized gas jet attack animation
            elif attacker.type == UnitType.GAS_MACHINIST and attack_target and target_unit:
                print(f"  [Renderer] *** GAS_MACHINIST ATTACK DETECTED ***")
                from boneglaive.graphical.animations.gas_machinist import GasMachinistPressurizedAttack

                gas_attack = GasMachinistPressurizedAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if gas_attack:
                    self.active_animations.append(gas_attack)
                    print(f"  [Animation] Successfully triggered GAS_MACHINIST pressurized gas attack animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create GAS_MACHINIST gas attack")

            # Check if attacker is DERELICTIONIST and trigger psychic void attack animation
            elif attacker.type == UnitType.DERELICTIONIST and attack_target and target_unit:
                print(f"  [Renderer] *** DERELICTIONIST ATTACK DETECTED ***")
                from boneglaive.graphical.animations.derelictionist import DerelictionistVoidAttack

                void_attack = DerelictionistVoidAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if void_attack:
                    self.active_animations.append(void_attack)
                    print(f"  [Animation] Successfully triggered DERELICTIONIST void attack animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create DERELICTIONIST void attack")

            # Check if attacker is POTPOURRIST and trigger aromatic potpourri scatter attack animation
            elif attacker.type == UnitType.POTPOURRIST and attack_target and target_unit:
                print(f"  [Renderer] *** POTPOURRIST ATTACK DETECTED ***")
                from boneglaive.graphical.animations.potpourrist import PotpourristAromaticAttack

                aromatic_attack = PotpourristAromaticAttack(
                    attacker_unit=attacker_animated,
                    target_unit=target_unit,
                    particle_emitter=self.particle_emitter,
                    screen_shake_callback=self.trigger_screen_shake
                )
                if aromatic_attack:
                    self.active_animations.append(aromatic_attack)
                    print(f"  [Animation] Successfully triggered POTPOURRIST aromatic scatter animation")
                else:
                    print(f"  [Animation] WARNING: Failed to create POTPOURRIST aromatic attack")

            # Check if TARGET has Riposte active (PELOTARI counterattack)
            # Use captured flag from BEFORE attack execution cleared it
            target_has_riposte = event.kwargs.get("target_has_riposte", False)

            if target_has_riposte and event.target_unit:
                print(f"  [Renderer] *** RIPOSTE COUNTERATTACK DETECTED on {event.target_unit.get_display_name()} ***")

                from boneglaive.graphical.animations.pelotari import RiposteAnimation
                from boneglaive.dlc.pelotari.physics import calculate_linear_trajectory

                # Calculate trajectories for 8 directions
                directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
                trajectories = []

                for direction in directions:
                    trajectory = calculate_linear_trajectory(
                        start_pos=(event.target_unit.y, event.target_unit.x),
                        direction=direction,
                        ricochet_mode=True,
                        max_range=12,  # 4 range * 3 for bounces
                        game=self.game_adapter.game,
                        max_bounces=2
                    )
                    trajectories.append(trajectory)

                # Get animated unit for target (PELOTARI)
                target_animated = self._find_animated_unit_by_game_unit(event.target_unit)

                if target_animated:
                    # Create Riposte animation
                    riposte_animation = RiposteAnimation(
                        caster_unit=target_animated,
                        trajectories=trajectories,
                        camera=self.camera,
                        particle_emitter=self.particle_emitter,
                        game=self.game_adapter.game
                    )

                    if riposte_animation:
                        self.active_animations.append(riposte_animation)
                        print(f"  [Animation] Successfully triggered Riposte counterattack with 8 pelotas")
                    else:
                        print(f"  [Animation] WARNING: Failed to create Riposte animation")
                else:
                    print(f"  [Animation] WARNING: Could not find animated unit for Riposte target")

            if attacker.type not in [UnitType.INTERFERER, UnitType.MANDIBLE_FOREMAN, UnitType.GLAIVEMAN,
                                      UnitType.GRAYMAN, UnitType.MARROW_CONDENSER, UnitType.FOWL_CONTRIVANCE,
                                      UnitType.DELPHIC_APPRAISER, UnitType.GAS_MACHINIST, UnitType.DERELICTIONIST,
                                      UnitType.POTPOURRIST] or not attack_target:
                print(f"  [DEBUG] Not a unit with special attack animation, or no attack target")

    def _create_skill_animation(self, event):
        """
        Create and queue a skill animation from an event.
        Helper method used by both handle_animation_event() and _show_event_immediately().

        Args:
            event: AnimationEvent with type "skill"
        """
        skill_name = event.kwargs.get("skill_name")
        caster = event.source_unit
        skill_target = event.kwargs.get("skill_target")  # (y, x) in game coords

        print(f"  [Renderer] Processing skill event: {skill_name} from {caster.get_display_name() if caster else 'None'}")

        # Find visual units
        caster_animated = self._get_visual_unit(caster)
        if caster_animated:
            caster_animated = caster_animated.animated_unit
            print(f"  [Renderer] Found caster visual unit at ({caster_animated.grid_x}, {caster_animated.grid_y})")
        else:
            print(f"  [Renderer] WARNING: Could not find visual unit for caster!")

        # Find target unit if any
        target_unit = None
        target_pos = None
        target_game_unit = event.target_unit  # Use unit captured before skill execution

        if skill_target:
            target_grid_x = skill_target[1]  # Convert (y,x) to (x,y)
            target_grid_y = skill_target[0]
            # NOTE: target_pos is in (grid_y, grid_x) format to match caster_grid_pos format in animations
            target_pos = (target_grid_y, target_grid_x)

            # Get visual unit - if event has target_game_unit, use it (unit may have moved)
            if target_game_unit:
                # Find the AnimatedUnit corresponding to this game unit
                target_unit = self._find_animated_unit_by_game_unit(target_game_unit)
                if target_unit:
                    print(f"  [Renderer] Found target visual unit via captured game unit: {target_unit.name}")
                else:
                    print(f"  [Renderer] WARNING: Could not find AnimatedUnit for captured game unit")
            else:
                # Fallback: try position lookup (for backwards compatibility with skills that don't capture target)
                target_unit = self._get_unit_at_grid(target_grid_x, target_grid_y)
                if target_unit:
                    target_game_unit = self.game_adapter.game.get_unit_at(skill_target[0], skill_target[1])
                    print(f"  [Renderer] Found target unit at position {skill_target}")
                else:
                    print(f"  [Renderer] No target unit found at {skill_target}")

        # Check for critical hit (Judgement on low HP target)
        is_crit = False
        if skill_name == "Judgement" and target_game_unit:
            from boneglaive.utils.constants import CRITICAL_HEALTH_PERCENT
            critical_threshold = int(target_game_unit.max_hp * CRITICAL_HEALTH_PERCENT)
            is_crit = target_game_unit.hp <= critical_threshold
            if is_crit:
                print(f"  [Animation] CRITICAL HIT detected! Target HP: {target_game_unit.hp}/{target_game_unit.max_hp}")

        # Get infused state from event (captured before skill execution)
        is_infused = event.kwargs.get("is_infused", False)
        if is_infused:
            print(f"  [Animation] INFUSED skill detected - using enhanced visuals!")

        # Get Matador bounce count if this is a Matador skill
        bounce_count = event.kwargs.get("bounce_count", 2)  # Default to 2 if not specified

        # Check if skill was reflected by Backhand
        if caster and hasattr(caster, 'skill_was_reflected') and caster.skill_was_reflected:
            caster.skill_was_reflected = False  # Reset flag
            return  # Don't create the original skill animation

        # Create animation via factory
        print(f"  [Renderer] Creating animation for {skill_name}...")

        # Extract additional kwargs to pass to factory (e.g., is_trap, trap_cone_positions)
        extra_kwargs = {}
        if 'is_trap' in event.kwargs:
            extra_kwargs['is_trap'] = event.kwargs['is_trap']
            print(f"  [Renderer] Trap mode detected: is_trap={extra_kwargs['is_trap']}")
        if 'trap_cone_positions' in event.kwargs:
            extra_kwargs['trap_cone_positions'] = event.kwargs['trap_cone_positions']
            print(f"  [Renderer] Using pre-calculated trap cone positions")

        animation = AnimationFactory.create_animation(
            skill_name,
            caster_unit=caster_animated,
            target_unit=target_unit,
            target_pos=target_pos,
            is_crit=is_crit,
            is_infused=is_infused,
            particle_emitter=self.particle_emitter,
            debris_list=self.debris_particles,
            screen_shake_callback=self.trigger_screen_shake,
            screen_flash_callback=self.trigger_screen_flash,
            units_list=self.units,
            camera=self.camera,
            game=self.game_adapter.game,  # Pass game for furniture detection & ricochet physics
            bounce_count=bounce_count,  # Pass bounce count for Matador animation
            **extra_kwargs  # Pass additional kwargs (is_trap, trap_cone_positions, etc.)
        )
        if animation:
            self.active_animations.append(animation)
            print(f"  [Animation] Successfully triggered {skill_name} animation" + (" (CRITICAL!)" if is_crit else ""))
        else:
            print(f"  [Animation] WARNING: Animation factory returned None for {skill_name}")

    def _create_glaive_sweep_animation(self, event):
        """
        Create Glaive Sweep counter-attack animation.

        Args:
            event: AnimationEvent with type "glaive_sweep"
        """
        from boneglaive.graphical.animations.glaiveman import GlaiveSweepAnimation

        caster = event.source_unit

        caster_animated = self._get_visual_unit(caster)
        if caster_animated:
            caster_animated = caster_animated.animated_unit
        else:
            return

        glaive_sweep_animation = GlaiveSweepAnimation(
            caster_unit=caster_animated,
            target_unit=None,
            target_pos=(caster.y, caster.x),
            is_crit=False,
            is_infused=False,
            particle_emitter=self.particle_emitter,
            debris_list=[],
            screen_shake_callback=self.trigger_screen_shake,
            screen_flash_callback=self.trigger_screen_flash,
            units_list=self.units,
            camera=self.camera,
            game=self.game_adapter.game
        )

        if glaive_sweep_animation:
            self.active_animations.append(glaive_sweep_animation)

    def _get_visual_unit(self, game_unit):
        """
        Get the VisualUnit for a given game unit.

        Args:
            game_unit: Game logic unit

        Returns:
            VisualUnit or None
        """
        if not game_unit:
            return None

        unit_id = self.game_adapter._get_unit_id(game_unit)
        return self.game_adapter.visual_units.get(unit_id)

    def _get_game_unit(self, animated_unit):
        """
        Get the game logic unit for a given animated unit.

        Args:
            animated_unit: AnimatedUnit from renderer

        Returns:
            Game logic Unit or None
        """
        if not animated_unit:
            return None

        # Search through visual units to find matching animated unit
        for visual_unit in self.game_adapter.visual_units.values():
            if visual_unit.animated_unit == animated_unit:
                return visual_unit.game_unit

        print(f"WARNING: Could not find game unit for {animated_unit.name}", flush=True)
        return None

    def _find_animated_unit_by_game_unit(self, game_unit):
        """
        Find the animated unit for a given game logic unit (reverse lookup).

        Args:
            game_unit: Game logic Unit

        Returns:
            AnimatedUnit or None
        """
        if not game_unit:
            return None

        # Search through visual units
        for visual_unit in self.game_adapter.visual_units.values():
            if visual_unit.game_unit == game_unit:
                return visual_unit.animated_unit

        return None

    def _get_unit_at_grid(self, grid_x: int, grid_y: int):
        """
        Find the animated unit at a specific grid position.

        Args:
            grid_x: Grid X coordinate (column)
            grid_y: Grid Y coordinate (row)

        Returns:
            AnimatedUnit or None
        """
        for unit in self.units:
            if unit.grid_x == grid_x and unit.grid_y == grid_y:
                return unit
        return None

    def _cycle_unit_selection(self, backwards: bool = False):
        """
        Cycle through the current player's units.

        Args:
            backwards: If True, cycle backwards (SHIFT+TAB), otherwise forward (TAB)
        """
        if not self.game_adapter.game:
            return

        # Get current player's alive units
        current_player = self.game_adapter.game.current_player
        player_units = [u for u in self.game_adapter.game.units
                       if u.player == current_player and u.is_alive()]

        if not player_units:
            return

        # Sort by position for consistent cycling (top-left to bottom-right)
        player_units.sort(key=lambda u: (u.y, u.x))

        # Find currently selected unit in the list
        current_index = -1
        if self.selected_unit:
            game_unit = self._get_game_unit(self.selected_unit)
            if game_unit in player_units:
                current_index = player_units.index(game_unit)

        # Cycle to next/previous unit
        if backwards:
            next_index = (current_index - 1) % len(player_units)
        else:
            next_index = (current_index + 1) % len(player_units)

        # Select the new unit
        next_game_unit = player_units[next_index]
        next_animated_unit = self._find_animated_unit_by_game_unit(next_game_unit)

        if next_animated_unit:
            # Select the unit
            self.selected_unit = next_animated_unit
            self.current_action_mode = "MOVE"

            # Update UI
            has_actions = any(u.move_target or u.attack_target or u.skill_target
                            for u in self.game_adapter.game.units if u.is_alive())
            self.action_menu.update(
                self.game_adapter.game,
                next_game_unit,
                self.current_action_mode,
                has_actions
            )
            self.skill_bar.update(next_animated_unit, next_game_unit)

            # Show movement range
            self.show_movement_range = True
            self.show_attack_range = False
            self.movement_positions = self.game_adapter.get_movement_range(next_game_unit)

    def draw(self):
        """Render the current frame."""
        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake_intensity > 0:
            shake_offset_x = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_offset_y = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)

        # Update camera shake offset (for animations that use camera)
        self.camera.set_shake(shake_offset_x, shake_offset_y)

        # Reuse main surface (performance: avoid allocation)
        main_surface = self._main_surface
        main_surface.fill(COLOR_BG)

        # Draw grid
        self.draw_grid(main_surface)

        # Draw revealed scalar node traps (after grid, before range indicators)
        self.draw_revealed_traps(main_surface)

        # Draw Rail Genesis junction indicators (after grid, before range indicators)
        self.draw_rail_junctions(main_surface)

        # Draw movement/target range indicators
        self.draw_range_indicators(main_surface)

        # Draw selection highlight (before units so it's behind them)
        if self.selected_unit:
            self.draw_selection_highlight(main_surface, self.selected_unit)

        # Draw astral values if DELPHIC APPRAISER is selected
        if self.show_astral_values:
            self.draw_astral_values(main_surface)

        # Draw imbued furniture effects (Market Futures)
        self.draw_imbued_furniture(main_surface)

        # Draw skill target indicator shadows (semi-transparent unit previews)
        self.draw_skill_shadows(main_surface)

        # Draw units
        for unit in self.units:
            # Skip units that are hidden during teleport animation
            if hasattr(unit, 'teleport_hidden') and unit.teleport_hidden:
                continue

            # Skip units at off-map positions (e.g., GAS_MACHINIST during Diverge)
            if unit.grid_x < 0 or unit.grid_y < 0 or unit.grid_x >= GRID_WIDTH or unit.grid_y >= GRID_HEIGHT:
                continue

            # During setup phase, hide opponent's units
            if self.setup_mode and self.game_adapter.game and self.game_adapter.game.setup_phase:
                setup_player = self.game_adapter.game.setup_player
                # Get the game unit to check player
                game_unit = self._get_game_unit(unit)
                if game_unit and game_unit.player != setup_player:
                    # Hide units from the other player during their setup
                    continue

            unit.draw(main_surface, self.small_font)

        # Draw target indicator pips on all tiles
        self.draw_target_pips(main_surface)

        # Draw background animations FIRST (zones, environmental effects - render below other animations)
        for animation in self.background_animations:
            animation.draw(main_surface)

        # Draw active animations
        for animation in self.active_animations:
            animation.draw(main_surface)

        # Draw particles
        self.particle_emitter.draw(main_surface)
        for text in self.floating_texts:
            text.draw(main_surface, self.font)
        if len(self.debris_particles) > 0 and not hasattr(self, '_debris_draw_logged'):
            print(f"[Renderer] Drawing {len(self.debris_particles)} debris particles")
            self._debris_draw_logged = True
        for debris in self.debris_particles:
            debris.draw(main_surface)

        # Draw skill bar (above map, below top bar) - only if show_skills is True
        if self.show_skills:
            self.skill_bar.draw(main_surface, SCREEN_WIDTH, SCREEN_HEIGHT, TOP_BAR_HEIGHT)

        # Draw combat log (below map, horizontal bar - maximized to fit space)
        combat_log_x = LEFT_PANEL_WIDTH + 10  # 290
        combat_log_y = GRID_OFFSET_Y + GAME_BOARD_HEIGHT + 10  # Below map with spacing
        self.combat_log.draw(main_surface, combat_log_x, combat_log_y, height=90, width=900)

        # Draw UI (includes all panels and components)
        self.draw_ui(main_surface)

        # Apply shake offset and blit to screen
        self.screen.fill(COLOR_BG)
        self.screen.blit(main_surface, (int(shake_offset_x), int(shake_offset_y)))

        # Draw flash overlay (performance: reuse surface)
        if self.flash_alpha > 0:
            self._flash_surface.set_alpha(int(self.flash_alpha))
            self._flash_surface.fill(self.flash_color)
            self.screen.blit(self._flash_surface, (0, 0))

        # Draw help page overlay (must be drawn last, on top of everything)
        self.help_page.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Draw message log window (on top of help page)
        self.message_log_window.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Draw upgrade window (on top of everything except help/message log)
        if self.upgrade_window.visible:
            self.upgrade_window.draw(self.screen)

        # Draw respawn window (on top of everything except help page and message log)
        if self.respawn_mode and self.respawn_selecting_unit:
            self.respawn_window.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Draw setup window (on top of everything except help page)
        if self.setup_mode and self.setup_selecting_unit:
            self.setup_window.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
            # Draw unit help panel - large horizontal panel to the right of setup window
            # Setup window: x=100, width=500, so ends at x=600
            help_panel_x = 620  # Start 20px after setup window
            help_panel_y = 50
            help_panel_width = SCREEN_WIDTH - help_panel_x - 20  # Fill remaining width
            help_panel_height = SCREEN_HEIGHT - 100
            self.setup_help_panel_rect = self.setup_unit_help.draw(self.screen, help_panel_x, help_panel_y, help_panel_width, help_panel_height)

        # Draw game over window (on top of everything - highest z-order)
        if self.game_over_window.visible:
            self.game_over_window.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Draw concede dialog (on top of game over window if both visible)
        if self.concede_dialog.visible:
            self.concede_dialog.draw(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Draw FPS counter (for troubleshooting)
        if self.show_fps:
            fps_text = f"FPS: {self.fps_display:.1f}"
            fps_surface = self.small_font.render(fps_text, True, (100, 255, 100))
            # Position in top-right corner with small padding
            fps_x = SCREEN_WIDTH - fps_surface.get_width() - 10
            fps_y = 5
            # Draw semi-transparent background
            bg_rect = pygame.Rect(fps_x - 5, fps_y - 2, fps_surface.get_width() + 10, fps_surface.get_height() + 4)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(180)
            bg_surface.fill((20, 20, 20))
            self.screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
            # Draw FPS text
            self.screen.blit(fps_surface, (fps_x, fps_y))

        pygame.display.flip()

    def mark_tile_dirty(self, x: int, y: int):
        """Mark a tile as needing redraw. Call this when terrain/furniture changes."""
        self._dirty_tiles.add((x, y))

    def mark_all_tiles_dirty(self):
        """Force full grid redraw on next frame."""
        self._grid_fully_dirty = True
        self._static_grid_surface = None

    @property
    def _grid_dirty(self):
        """Legacy property for compatibility - always returns True if grid is dirty."""
        return self._grid_fully_dirty

    @_grid_dirty.setter
    def _grid_dirty(self, value: bool):
        """Legacy setter - redirects to _grid_fully_dirty for compatibility."""
        if value:
            self.mark_all_tiles_dirty()
        # If setting to False, we ignore it since the new system auto-clears dirty flags

    def _is_furniture(self, terrain_type: TerrainType) -> bool:
        """Check if a terrain type is furniture (should render on top of base terrain)."""
        furniture_types = [
            TerrainType.RADIO_CONSOLE, TerrainType.COAT_RACK, TerrainType.OTTOMAN,
            TerrainType.CONSOLE, TerrainType.CURIOSITY_SHELF, TerrainType.TIFFANY_LAMP,
            TerrainType.EASEL, TerrainType.SCULPTURE, TerrainType.BENCH,
            TerrainType.PODIUM, TerrainType.VASE, TerrainType.WORKBENCH,
            TerrainType.COUCH, TerrainType.TOOLBOX, TerrainType.COT,
            TerrainType.CONVEYOR, TerrainType.MINI_PUMPKIN, TerrainType.POTPOURRI_BOWL
        ]
        return terrain_type in furniture_types

    def _get_base_terrain_for_map(self, game_map) -> TerrainType:
        """Get the base terrain type for the current map (to render under furniture)."""
        if not game_map or not hasattr(game_map, 'name'):
            return TerrainType.EMPTY

        map_name = game_map.name.lower()

        # Map name to base terrain mapping
        if 'hard' in map_name or 'pressed' in map_name:
            return TerrainType.CONCRETE_FLOOR
        elif 'stained' in map_name or 'stone' in map_name:
            return TerrainType.CANYON_FLOOR
        elif 'lime' in map_name or 'foyer' in map_name:
            return TerrainType.DUST
        else:
            # Default to empty for unknown maps
            return TerrainType.EMPTY

    def _render_single_tile(self, surface: pygame.Surface, x: int, y: int, game_map):
        """Render a single tile (used for dirty rectangle updates)."""
        # Calculate tile position (relative to grid surface, not screen)
        tile_x = x * TILE_SIZE
        tile_y = y * TILE_SIZE
        rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)

        # Get terrain type at this position
        terrain_type = TerrainType.EMPTY
        if game_map:
            terrain_type = game_map.get_terrain_at(y, x)

        # For rail tiles, render the underlying terrain instead
        if terrain_type == TerrainType.RAIL and game_map:
            terrain_type = game_map.get_rail_original_terrain(y, x)

        # Determine base color (checkerboard pattern)
        base_color = COLOR_GRID_DARK if (x + y) % 2 == 0 else COLOR_GRID_LIGHT

        # Highlight hovered tile
        if self.hovered_grid_pos == (x, y):
            base_color = tuple(min(255, c + 30) for c in base_color)

        # Draw base tile
        pygame.draw.rect(surface, base_color, rect)

        # Check if this is furniture - if so, render base terrain first
        is_furniture = self._is_furniture(terrain_type)
        if is_furniture and game_map:
            # Get the base terrain for this map
            base_terrain = self._get_base_terrain_for_map(game_map)
            if base_terrain != TerrainType.EMPTY:
                # Render base terrain texture underneath furniture
                base_surface = self._load_terrain_tile(base_terrain)
                if base_surface:
                    surface.blit(base_surface, (tile_x, tile_y))

        # Try to load and draw terrain/furniture SVG
        if terrain_type != TerrainType.EMPTY:
            terrain_surface = self._load_terrain_tile(terrain_type)
            if terrain_surface:
                surface.blit(terrain_surface, (tile_x, tile_y))

                # Add player-colored outline for MARROW_WALL
                if terrain_type == TerrainType.MARROW_WALL:
                    if hasattr(self.game_adapter.game, 'marrow_dike_tiles'):
                        pos_tuple = (y, x)
                        if pos_tuple in self.game_adapter.game.marrow_dike_tiles:
                            wall_info = self.game_adapter.game.marrow_dike_tiles[pos_tuple]
                            if 'owner' in wall_info and wall_info['owner']:
                                if wall_info['owner'].player == 1:
                                    outline_color = (0, 255, 100)
                                else:
                                    outline_color = (100, 150, 255)
                                pygame.draw.rect(surface, outline_color, rect, 2)
            else:
                # Fallback: draw colored rectangle
                if terrain_type in [TerrainType.LIMESTONE, TerrainType.PILLAR,
                                   TerrainType.STAINED_STONE, TerrainType.HYDRAULIC_PRESS]:
                    pygame.draw.rect(surface, (80, 80, 90), rect)
                elif terrain_type in [TerrainType.DUST, TerrainType.CANYON_FLOOR, TerrainType.CONCRETE_FLOOR]:
                    pygame.draw.rect(surface, (70, 75, 80), rect)
                else:
                    pygame.draw.rect(surface, (100, 110, 120), rect)

        # Draw grid lines
        pygame.draw.rect(surface, (30, 34, 42), rect, 1)

        # Draw rail overlay if needed
        if game_map and self.rail_universal and game_map.get_terrain_at(y, x) == TerrainType.RAIL:
            surface.blit(self.rail_universal, (tile_x, tile_y))

    def draw_grid(self, surface: pygame.Surface):
        """
        Draw the game grid with terrain and furniture.
        OPTIMIZED: Uses dirty rectangle tracking to only redraw changed tiles.
        """
        game_map = self.game_adapter.game.map if self.game_adapter.game else None

        # Full redraw if needed (first frame or major change)
        if self._grid_fully_dirty or self._static_grid_surface is None:
            # Create cached surface if needed
            if self._static_grid_surface is None:
                grid_width = GRID_WIDTH * TILE_SIZE
                grid_height = GRID_HEIGHT * TILE_SIZE
                self._static_grid_surface = pygame.Surface((grid_width, grid_height))

            # Render all tiles to cache
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    self._render_single_tile(self._static_grid_surface, x, y, game_map)

            self._grid_fully_dirty = False
            self._dirty_tiles.clear()

        # Update only dirty tiles
        elif self._dirty_tiles:
            for x, y in self._dirty_tiles:
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    self._render_single_tile(self._static_grid_surface, x, y, game_map)
            self._dirty_tiles.clear()

        # Blit cached grid to main surface
        surface.blit(self._static_grid_surface, (GRID_OFFSET_X, GRID_OFFSET_Y))

    def draw_grid_old(self, surface: pygame.Surface):
        """
        OLD IMPLEMENTATION - kept for reference.
        Draw the game grid with terrain and furniture using two-pass rendering for rails.
        """
        # Get game map if available
        game_map = self.game_adapter.game.map if self.game_adapter.game else None

        # PASS 1: Draw base terrain and furniture
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                # Calculate tile position (relative to grid surface, not screen)
                tile_x = x * TILE_SIZE
                tile_y = y * TILE_SIZE
                rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)

                # Get terrain type at this position
                terrain_type = TerrainType.EMPTY
                if game_map:
                    terrain_type = game_map.get_terrain_at(y, x)

                # For rail tiles, render the underlying terrain instead
                if terrain_type == TerrainType.RAIL and game_map:
                    # Get original terrain before rail was placed
                    terrain_type = game_map.get_rail_original_terrain(y, x)

                # Determine base color (checkerboard pattern for empty/passable tiles)
                base_color = COLOR_GRID_DARK if (x + y) % 2 == 0 else COLOR_GRID_LIGHT

                # Draw base tile
                pygame.draw.rect(self._grid_surface, base_color, rect)

                # Try to load and draw terrain/furniture SVG
                if terrain_type != TerrainType.EMPTY:
                    terrain_surface = self._load_terrain_tile(terrain_type)
                    if terrain_surface:
                        # Blit the SVG surface at tile position
                        self._grid_surface.blit(terrain_surface, (tile_x, tile_y))

                        # Add player-colored outline for MARROW_WALL
                        if terrain_type == TerrainType.MARROW_WALL:
                            if hasattr(self.game_adapter.game, 'marrow_dike_tiles'):
                                pos_tuple = (y, x)
                                if pos_tuple in self.game_adapter.game.marrow_dike_tiles:
                                    wall_info = self.game_adapter.game.marrow_dike_tiles[pos_tuple]
                                    if 'owner' in wall_info and wall_info['owner']:
                                        # Use owner's player color for outline
                                        if wall_info['owner'].player == 1:
                                            outline_color = (0, 255, 100)  # Green
                                        else:
                                            outline_color = (100, 150, 255)  # Blue

                                        # Draw outline around the tile (same as units)
                                        pygame.draw.rect(self._grid_surface, outline_color, rect, 2)
                    else:
                        # Fallback: draw a colored rectangle to indicate terrain/furniture
                        # Use different colors for different types
                        if terrain_type in [TerrainType.LIMESTONE, TerrainType.PILLAR,
                                           TerrainType.STAINED_STONE, TerrainType.HYDRAULIC_PRESS]:
                            # Blocking terrain - dark gray
                            pygame.draw.rect(self._grid_surface, (80, 80, 90), rect)
                        elif terrain_type in [TerrainType.DUST, TerrainType.CANYON_FLOOR, TerrainType.CONCRETE_FLOOR]:
                            # Passable terrain - slightly different shade
                            pygame.draw.rect(self._grid_surface, (70, 75, 80), rect)
                        else:
                            # Furniture - lighter color
                            pygame.draw.rect(self._grid_surface, (100, 110, 120), rect)

                # Draw grid lines
                pygame.draw.rect(self._grid_surface, (30, 34, 42), rect, 1)

        # PASS 2: Draw universal rail bomb overlays on top of terrain
        if game_map and self.rail_universal:
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    terrain_type = game_map.get_terrain_at(y, x)

                    if terrain_type == TerrainType.RAIL:
                        # Calculate tile position (relative to grid surface)
                        tile_x = x * TILE_SIZE
                        tile_y = y * TILE_SIZE

                        # Blit the universal rail bomb overlay
                        self._grid_surface.blit(self.rail_universal, (tile_x, tile_y))

    def draw_revealed_traps(self, surface: pygame.Surface):
        """Draw revealed scalar node traps and Fragcrest traps on the map."""
        # Draw revealed scalar node traps
        if self.game_adapter.game and hasattr(self.game_adapter.game, 'scalar_nodes'):
            # Get revealed nodes from game state adapter
            revealed_nodes = getattr(self.game_adapter, 'revealed_scalar_nodes', set())

            # If trap overlay loaded, draw each revealed trap
            if self.scalar_node_trap:
                for node_pos in revealed_nodes:
                    y, x = node_pos

                    # Calculate tile position
                    tile_x = GRID_OFFSET_X + x * TILE_SIZE
                    tile_y = GRID_OFFSET_Y + y * TILE_SIZE

                    # Blit the scalar node trap overlay
                    surface.blit(self.scalar_node_trap, (tile_x, tile_y))

        # Draw revealed Fragcrest traps
        if self.game_adapter.game and hasattr(self.game_adapter.game, 'fragcrest_traps'):
            # If trap overlay loaded, draw each revealed trap
            if self.fragcrest_trap:
                for trap_pos, trap_info in self.game_adapter.game.fragcrest_traps.items():
                    # Only draw if trap is revealed
                    if trap_info.get('revealed', False):
                        y, x = trap_pos

                        # Calculate tile position
                        tile_x = GRID_OFFSET_X + x * TILE_SIZE
                        tile_y = GRID_OFFSET_Y + y * TILE_SIZE

                        # Blit the Fragcrest trap overlay
                        surface.blit(self.fragcrest_trap, (tile_x, tile_y))

    def draw_rail_junctions(self, surface: pygame.Surface):
        """Draw Rail Genesis junction indicators for upgraded FOWL_CONTRIVANCE."""
        if not self.game_adapter.game or not self.rail_junction_overlay:
            return

        # Only show for current player's upgraded FOWL_CONTRIVANCE
        current_player = self.game_adapter.game.current_player
        has_rail_genesis = False

        for unit in self.game_adapter.game.units:
            if (unit.is_alive() and
                unit.type == UnitType.FOWL_CONTRIVANCE and
                unit.player == current_player):
                from boneglaive.game.upgrades import UpgradeManager
                if UpgradeManager.is_skill_upgraded(unit, "Rail Genesis"):
                    has_rail_genesis = True
                    break

        if not has_rail_genesis:
            return

        # Calculate junction positions (same logic as engine.py:2403-2421)
        center_y = self.game_adapter.game.map.height // 2
        center_x = self.game_adapter.game.map.width // 2

        top_horizontal = 1
        middle_horizontal = center_y - 2
        bottom_horizontal = self.game_adapter.game.map.height - 2

        vertical_line_1 = center_x - 2
        vertical_line_2 = center_x + 2

        junction_coords = [
            (top_horizontal, vertical_line_1),
            (top_horizontal, vertical_line_2),
            (middle_horizontal, vertical_line_1),
            (middle_horizontal, vertical_line_2),
            (bottom_horizontal, vertical_line_1),
            (bottom_horizontal, vertical_line_2)
        ]

        # Pulsing effect (subtle, 2-second cycle)
        import math
        pulse = (math.sin(self.junction_pulse_time * math.pi) + 1) * 0.5
        alpha = int(100 + pulse * 80)  # Range: 100-180

        overlay = self.rail_junction_overlay.copy()
        overlay.set_alpha(alpha)

        # Draw overlay at each junction
        for y, x in junction_coords:
            tile_x = GRID_OFFSET_X + x * TILE_SIZE
            tile_y = GRID_OFFSET_Y + y * TILE_SIZE
            surface.blit(overlay, (tile_x, tile_y))

    def draw_range_indicators(self, surface: pygame.Surface):
        """Draw movement range, attack range, and skill range indicators."""
        # Performance: Reuse cached surface instead of creating new one
        indicator_surf = self._indicator_surf
        indicator_rect = indicator_surf.get_rect()

        # Draw movement range (green)
        if self.show_movement_range and self.valid_positions:
            for grid_x, grid_y in self.valid_positions:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*COLOR_MOVEMENT, 80), indicator_rect)
                pygame.draw.rect(indicator_surf, (*COLOR_MOVEMENT, 150), indicator_rect, 2)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + grid_x * TILE_SIZE, GRID_OFFSET_Y + grid_y * TILE_SIZE)
                )

        # Draw attack range (red)
        if self.show_target_range and self.attack_positions:
            for grid_x, grid_y in self.attack_positions:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*COLOR_TARGET, 80), indicator_rect)
                pygame.draw.rect(indicator_surf, (*COLOR_TARGET, 150), indicator_rect, 2)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + grid_x * TILE_SIZE, GRID_OFFSET_Y + grid_y * TILE_SIZE)
                )

        # Draw skill range (purple)
        if self.show_skill_range and self.skill_positions:
            skill_color = (140, 80, 200)  # Darker purple for skills (matches pip color)
            for grid_x, grid_y in self.skill_positions:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*skill_color, 120), indicator_rect)  # Less transparent
                pygame.draw.rect(indicator_surf, (*skill_color, 200), indicator_rect, 2)  # Less transparent border
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + grid_x * TILE_SIZE, GRID_OFFSET_Y + grid_y * TILE_SIZE)
                )

        # Draw respawn valid tiles (cyan/green)
        if self.respawn_selecting_location and self.respawn_valid_tiles:
            respawn_color = (100, 255, 150)  # Green for respawn
            for y, x in self.respawn_valid_tiles:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*respawn_color, 80), indicator_rect)
                pygame.draw.rect(indicator_surf, (*respawn_color, 180), indicator_rect, 3)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + x * TILE_SIZE, GRID_OFFSET_Y + y * TILE_SIZE)
                )

        # Draw respawn ghost preview
        if self.respawn_selecting_location and self.respawn_ghost_pos and self.selected_dead_unit:
            ghost_x, ghost_y = self.respawn_ghost_pos

            # Check if position is valid (game logic uses (y, x) format)
            pos_valid = (ghost_y, ghost_x) in self.respawn_valid_tiles if hasattr(self, 'respawn_valid_tiles') else True

            # Get sprite path for the selected unit type
            sprite_path = self._get_sprite_path(self.selected_dead_unit.unit_type)

            # Try to load and display the sprite
            if sprite_path and os.path.exists(sprite_path):
                try:
                    # Load sprite
                    if sprite_path.endswith('.svg'):
                        import cairosvg
                        from io import BytesIO
                        png_data = cairosvg.svg2png(url=sprite_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
                        sprite = pygame.image.load(BytesIO(png_data))
                    else:
                        sprite = pygame.image.load(sprite_path)
                        sprite = pygame.transform.smoothscale(sprite, (TILE_SIZE, TILE_SIZE))

                    # Create ghost surface with semi-transparent sprite
                    ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

                    # Draw sprite with transparency
                    sprite_copy = sprite.copy()
                    sprite_copy.set_alpha(120)  # Semi-transparent
                    ghost_surf.blit(sprite_copy, (0, 0))

                    # Add colored tint overlay (green for respawn)
                    tint_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    if pos_valid:
                        tint_surf.fill((100, 255, 150, 60))  # Green tint for valid respawn
                    else:
                        tint_surf.fill((255, 100, 100, 60))  # Red tint for invalid
                    ghost_surf.blit(tint_surf, (0, 0))

                    # Draw the ghost preview
                    surface.blit(
                        ghost_surf,
                        (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE)
                    )
                except Exception as e:
                    # Fallback to text if sprite loading fails
                    print(f"Could not load sprite for respawn ghost preview: {e}")
                    ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    ghost_surf.fill((100, 255, 150, 60))  # Green tint
                    if hasattr(self.selected_dead_unit, 'unit_type'):
                        unit_type_name = self.selected_dead_unit.unit_type.name if hasattr(self.selected_dead_unit.unit_type, 'name') else str(self.selected_dead_unit.unit_type)
                        text = self.small_font.render(unit_type_name[:3], True, (255, 255, 255))
                        text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
                        ghost_surf.blit(text, text_rect)
                    surface.blit(ghost_surf, (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE))
            else:
                # Fallback to text if no sprite path found
                ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                ghost_surf.fill((100, 255, 150, 60))  # Green tint
                if hasattr(self.selected_dead_unit, 'unit_type'):
                    unit_type_name = self.selected_dead_unit.unit_type.name if hasattr(self.selected_dead_unit.unit_type, 'name') else str(self.selected_dead_unit.unit_type)
                    text = self.small_font.render(unit_type_name[:3], True, (255, 255, 255))
                    text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
                    ghost_surf.blit(text, text_rect)
                surface.blit(ghost_surf, (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE))

        # Draw queued respawn ghosts (after confirmation, before execution)
        if self.game_adapter.game:
            for dead_unit in self.game_adapter.game.dead_units:
                if hasattr(dead_unit, 'respawn_preview') and dead_unit.respawn_preview:
                    # respawn_preview is in (y, x) format, convert to (grid_x, grid_y) for drawing
                    ghost_y, ghost_x = dead_unit.respawn_preview

                    # Get sprite path for the unit type
                    sprite_path = self._get_sprite_path(dead_unit.unit_type)

                    # Try to load and display the sprite
                    if sprite_path and os.path.exists(sprite_path):
                        try:
                            # Load sprite
                            if sprite_path.endswith('.svg'):
                                import cairosvg
                                from io import BytesIO
                                png_data = cairosvg.svg2png(url=sprite_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
                                sprite = pygame.image.load(BytesIO(png_data))
                            else:
                                sprite = pygame.image.load(sprite_path)
                                sprite = pygame.transform.smoothscale(sprite, (TILE_SIZE, TILE_SIZE))

                            # Create ghost surface with semi-transparent sprite
                            ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

                            # Draw sprite with transparency
                            sprite_copy = sprite.copy()
                            sprite_copy.set_alpha(120)  # Semi-transparent
                            ghost_surf.blit(sprite_copy, (0, 0))

                            # Add colored tint overlay (green for queued respawn)
                            tint_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                            tint_surf.fill((100, 255, 150, 60))  # Green tint
                            ghost_surf.blit(tint_surf, (0, 0))

                            # Draw the ghost preview
                            surface.blit(
                                ghost_surf,
                                (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE)
                            )
                        except Exception as e:
                            # Fallback to text if sprite loading fails
                            print(f"Could not load sprite for queued respawn ghost: {e}")
                            ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                            ghost_surf.fill((100, 255, 150, 60))  # Green tint
                            if hasattr(dead_unit, 'unit_type'):
                                unit_type_name = dead_unit.unit_type.name if hasattr(dead_unit.unit_type, 'name') else str(dead_unit.unit_type)
                                text = self.small_font.render(unit_type_name[:3], True, (255, 255, 255))
                                text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
                                ghost_surf.blit(text, text_rect)
                            surface.blit(ghost_surf, (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE))
                    else:
                        # Fallback to text if no sprite path found
                        ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        ghost_surf.fill((100, 255, 150, 60))  # Green tint
                        if hasattr(dead_unit, 'unit_type'):
                            unit_type_name = dead_unit.unit_type.name if hasattr(dead_unit.unit_type, 'name') else str(dead_unit.unit_type)
                            text = self.small_font.render(unit_type_name[:3], True, (255, 255, 255))
                            text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
                            ghost_surf.blit(text, text_rect)
                        surface.blit(ghost_surf, (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE))

        # Draw setup valid tiles (blue/cyan)
        if self.setup_placing_unit and self.setup_valid_tiles:
            setup_color = (100, 200, 255)  # Blue/cyan for setup
            for y, x in self.setup_valid_tiles:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*setup_color, 80), indicator_rect)
                pygame.draw.rect(indicator_surf, (*setup_color, 200), indicator_rect, 3)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + x * TILE_SIZE, GRID_OFFSET_Y + y * TILE_SIZE)
                )

        # Draw setup ghost preview
        if self.setup_placing_unit and self.setup_ghost_pos and self.selected_unit_type:
            ghost_x, ghost_y = self.setup_ghost_pos  # screen_to_grid returns (grid_x, grid_y)

            # Check if position is valid (game logic uses (y, x) format)
            pos_valid = (ghost_y, ghost_x) in self.setup_valid_tiles

            # Get sprite path for the selected unit type
            sprite_path = self._get_sprite_path(self.selected_unit_type)

            # Try to load and display the sprite
            if sprite_path and os.path.exists(sprite_path):
                try:
                    # Load sprite
                    if sprite_path.endswith('.svg'):
                        import cairosvg
                        from io import BytesIO
                        png_data = cairosvg.svg2png(url=sprite_path, output_width=TILE_SIZE, output_height=TILE_SIZE)
                        sprite = pygame.image.load(BytesIO(png_data))
                    else:
                        sprite = pygame.image.load(sprite_path)
                        sprite = pygame.transform.smoothscale(sprite, (TILE_SIZE, TILE_SIZE))

                    # Create ghost surface with semi-transparent sprite
                    ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

                    # Draw sprite with transparency
                    sprite_copy = sprite.copy()
                    sprite_copy.set_alpha(120)  # Semi-transparent
                    ghost_surf.blit(sprite_copy, (0, 0))

                    # Add colored tint overlay
                    tint_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    if pos_valid:
                        tint_surf.fill((100, 200, 255, 60))  # Blue tint for valid
                    else:
                        tint_surf.fill((255, 100, 100, 60))  # Red tint for invalid
                    ghost_surf.blit(tint_surf, (0, 0))

                    # Draw the ghost preview
                    surface.blit(
                        ghost_surf,
                        (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE)
                    )
                except Exception as e:
                    # Fallback to text if sprite loading fails
                    print(f"Could not load sprite for ghost preview: {e}")
                    ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    if pos_valid:
                        ghost_surf.fill((100, 200, 255, 80))
                    else:
                        ghost_surf.fill((255, 100, 100, 80))
                    unit_display_name = self.setup_window.unit_names.get(self.selected_unit_type, str(self.selected_unit_type))
                    text = self.small_font.render(unit_display_name[:3], True, (255, 255, 255))
                    text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
                    ghost_surf.blit(text, text_rect)
                    surface.blit(ghost_surf, (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE))
            else:
                # Fallback to text if sprite path not found
                ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                if pos_valid:
                    ghost_surf.fill((100, 200, 255, 80))
                else:
                    ghost_surf.fill((255, 100, 100, 80))
                unit_display_name = self.setup_window.unit_names.get(self.selected_unit_type, str(self.selected_unit_type))
                text = self.small_font.render(unit_display_name[:3], True, (255, 255, 255))
                text_rect = text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
                ghost_surf.blit(text, text_rect)
                surface.blit(ghost_surf, (GRID_OFFSET_X + ghost_x * TILE_SIZE, GRID_OFFSET_Y + ghost_y * TILE_SIZE))

    def draw_ui(self, surface: pygame.Surface):
        """Draw UI elements using new three-zone layout."""
        # Update UI components with current game state
        game = self.game_adapter.game
        if game:
            # Get selected game unit (not visual unit)
            selected_game_unit = None
            if self.selected_unit:
                # Find corresponding game unit
                for unit in game.units:
                    if unit.is_alive() and unit.x == self.selected_unit.grid_x and unit.y == self.selected_unit.grid_y:
                        selected_game_unit = unit
                        break

            # Update top bar
            self.top_bar.update(game, self.current_action_mode)

            # Update unit status bar
            self.unit_status_bar.update(game, selected_game_unit)

            # Update action menu
            has_actions = any(u.move_target or u.attack_target or u.skill_target for u in game.units if u.is_alive())
            self.action_menu.update(game, selected_game_unit, self.current_action_mode, has_actions)

        # Draw top bar (full width)
        self.top_bar.draw(surface, SCREEN_WIDTH)

        # Calculate available height for side panels
        panel_height = SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT

        # Check UI layout setting from config
        config = ConfigManager()
        ui_layout = config.get('ui_layout', 'default')

        # === LEFT PANEL (Dedicated Space) ===
        left_panel_x = 0  # Starts at left edge
        left_panel_y = TOP_BAR_HEIGHT

        # Draw solid background (performance: reuse cached surface)
        self._left_panel_surface.fill((30, 34, 42))  # Solid dark background
        surface.blit(self._left_panel_surface, (left_panel_x, left_panel_y))

        # Draw border on right side
        pygame.draw.line(surface, (60, 64, 72),
                        (LEFT_PANEL_WIDTH - 1, TOP_BAR_HEIGHT),
                        (LEFT_PANEL_WIDTH - 1, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT), 2)

        if ui_layout == "reversed":
            # Draw turn counter, motor, and action menu on left panel
            turn_y = left_panel_y + 10
            self._draw_turn_counter(surface, left_panel_x, turn_y)
            motor_y = turn_y + 40
            self.motor_animation.draw(surface, left_panel_x + 15, motor_y)
            action_menu_y = motor_y + 190
            self.action_menu.draw(surface, left_panel_x + 5, action_menu_y)
        else:
            # Draw player indicator, unit status bar, and unit info on left panel
            player_y = left_panel_y + 5
            self._draw_player_indicator(surface, left_panel_x, player_y)
            unit_bar_y = player_y + 35
            unit_bar_height = self.unit_status_bar.get_height()
            self.unit_status_bar.draw(surface, left_panel_x + 5, unit_bar_y)
            unit_info_y = unit_bar_y + unit_bar_height + 15
            self.unit_info_panel.draw(surface, left_panel_x + 10, unit_info_y)

        # === RIGHT PANEL (Dedicated Space) ===
        right_panel_x = SCREEN_WIDTH - RIGHT_PANEL_WIDTH  # Starts at right edge - panel width
        right_panel_y = TOP_BAR_HEIGHT

        # Draw solid background (performance: reuse cached surface)
        self._right_panel_surface.fill((30, 34, 42))  # Solid dark background
        surface.blit(self._right_panel_surface, (right_panel_x, right_panel_y))

        # Draw border on left side
        pygame.draw.line(surface, (60, 64, 72),
                        (right_panel_x, TOP_BAR_HEIGHT),
                        (right_panel_x, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT), 2)

        if ui_layout == "reversed":
            # Draw player indicator, unit status bar, and unit info on right panel
            player_y = right_panel_y + 5
            self._draw_player_indicator(surface, right_panel_x, player_y)
            unit_bar_y = player_y + 35
            unit_bar_height = self.unit_status_bar.get_height()
            self.unit_status_bar.draw(surface, right_panel_x + 5, unit_bar_y)
            unit_info_y = unit_bar_y + unit_bar_height + 15
            self.unit_info_panel.draw(surface, right_panel_x + 10, unit_info_y)
        else:
            # Draw turn counter, motor, and action menu on right panel
            turn_y = right_panel_y + 10
            self._draw_turn_counter(surface, right_panel_x, turn_y)
            motor_y = turn_y + 40
            self.motor_animation.draw(surface, right_panel_x + 15, motor_y)
            action_menu_y = motor_y + 190
            self.action_menu.draw(surface, right_panel_x + 5, action_menu_y)

    def _draw_turn_counter(self, surface: pygame.Surface, x: int, y: int):
        """Draw turn counter (works on either panel)."""
        from .ui.font_utils import render_fitted_text

        game = self.game_adapter.game
        if not game:
            return

        # Panel width is same for both sides
        panel_width = LEFT_PANEL_WIDTH  # Same as RIGHT_PANEL_WIDTH

        # Draw "TURN X" centered in panel
        turn_text = render_fitted_text(
            f"TURN {game.turn}",
            max_width=panel_width - 20,
            max_height=25,
            color=(255, 255, 255),
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )
        text_rect = turn_text.get_rect(center=(x + panel_width // 2, y + 15))
        surface.blit(turn_text, text_rect)

    def _draw_player_indicator(self, surface: pygame.Surface, x: int, y: int):
        """Draw player indicator (works on either panel)."""
        from .ui.font_utils import render_fitted_text

        game = self.game_adapter.game
        if not game:
            return

        # Panel width is same for both sides
        panel_width = LEFT_PANEL_WIDTH  # Same as RIGHT_PANEL_WIDTH

        # Get player color
        player_color = (100, 255, 100) if game.current_player == 1 else (100, 150, 255)
        player_name = game.get_player_name(game.current_player)

        # Draw player name centered in panel
        player_text = render_fitted_text(
            player_name.upper(),
            max_width=panel_width - 20,
            max_height=25,
            color=player_color,
            base_font_size=20,
            min_font_size=16,
            max_font_size=24
        )
        text_rect = player_text.get_rect(center=(x + panel_width // 2, y + 12))
        surface.blit(player_text, text_rect)

    def _apply_player2_first_turn_buff(self):
        """Apply +1 move range buff to all player 2 units on their first turn."""
        from boneglaive.utils.message_log import message_log, MessageType

        # Find all player 2 units and apply the buff
        player2_units = [unit for unit in self.game_adapter.game.units if unit.player == 2 and unit.is_alive()]

        if player2_units:
            # Apply the buff to each unit
            for unit in player2_units:
                # Check if unit is immune to status effects (GRAYMAN with Stasiality)
                if unit.is_immune_to_effects():
                    print(f"[FirstTurnBuff] {unit.get_display_name()} is immune to first turn bonus due to Stasiality")
                    continue

                # Add the move bonus (+1)
                unit.move_range_bonus += 1
                # Add a flag to show the status effect icon
                unit.first_turn_move_bonus = True
                # Set duration to 1 turn (consistent with other status effects)
                unit.first_turn_move_bonus_duration = 1

            # Show status effect icon flash for each buffed unit
            for unit in player2_units:
                if hasattr(unit, 'first_turn_move_bonus') and unit.first_turn_move_bonus:
                    # Find the animated unit for the visual flash using proper unit ID
                    unit_id = self.game_adapter._get_unit_id(unit)
                    if unit_id in self.game_adapter.visual_units:
                        visual_unit = self.game_adapter.visual_units[unit_id]
                        animated_unit = visual_unit.animated_unit
                        self._create_status_icon_flash(animated_unit, "first_turn_move_bonus")
                        print(f"[FirstTurnBuff] Created status icon flash for {unit.get_display_name()}")
                    else:
                        print(f"[FirstTurnBuff] WARNING: Could not find visual unit for {unit.get_display_name()}, unit_id={unit_id}")

            # Log the buff application
            message_log.add_system_message("Player 2 units receive +1 move range for going second!")
            self.combat_log.add_message("Player 2 units receive +1 move range for going second!", "system")
            print(f"[FirstTurnBuff] Applied +1 move range to {len(player2_units)} player 2 units")

    def execute_turn(self):
        """Execute the current turn (process all planned actions)."""
        if not self.game_adapter.game:
            print("ERROR: No game instance")
            return

        # Start motor animation
        self.motor_animation.start()

        # Log turn start
        self.combat_log.add_message(
            f"Turn {self.game_adapter.game.turn} - Player {self.game_adapter.game.current_player}",
            msg_type="system"
        )

        # Clear selection and skill mode
        self.selected_unit = None
        self.selected_skill = None
        self.show_movement_range = False
        self.show_target_range = False
        self.show_skill_range = False
        self.show_skills = False  # Hide skill bar
        self.show_astral_values = False  # Hide astral values on turn execution
        self.valid_positions = []
        self.attack_positions = []
        self.skill_positions = []
        self.skill_bar.update(None, None)

        # Execute turn in game logic (headless - no blocking UI callbacks)
        # Skill animations will be triggered by detecting skill usage in sync_state
        self.game_adapter.executing_turn = True
        self.game_adapter.post_execution_sync = False  # Flag to skip attack animations in pre-sync

        # Sync state BEFORE turn execution to catch planned skills
        pre_events = self.game_adapter.sync_state()
        for event in pre_events:
            self.handle_animation_event(event)

        # Check if any pre-execution events are blocking (must complete before game logic)
        has_blocking_animations = any(
            event.event_type == "skill" and
            event.kwargs.get("skill_name") in PRE_EXECUTION_BLOCKING_SKILLS
            for event in pre_events
        )

        if has_blocking_animations:
            # Flush ONLY blocking skills and damage events
            # Keep non-blocking skills (like Expedite) for post-execution when positions are correct
            self.flush_pending_events(only_blocking=True)

            # Wait for animations to complete
            frames_waited = 0
            while self.has_active_animations():
                delta_time = self.clock.tick(60) / 1000.0
                frames_waited += 1

                # Update only animations and visual effects (no game state sync)
                self._update_animations_only(delta_time)

                # Draw frame
                self.draw()
                pygame.display.flip()

        # Capture status effects snapshot BEFORE turn execution
        # This allows us to detect status effects that are applied and then cleared during execute_turn
        self.game_adapter.snapshot_status_effects()

        # Capture unit positions BEFORE turn execution
        # This allows us to detect if movement skills (Vault, Delta Config, etc.) succeeded
        self.game_adapter.snapshot_unit_positions()

        self.game_adapter.game.execute_turn(ui=None)

        # Sync state AFTER turn execution
        self.game_adapter.post_execution_sync = True  # Now detect attack animations
        post_events = self.game_adapter.sync_state()

        # Process zone_create and building_create events FIRST so they appear immediately before skill animations
        # This ensures persistent zone/building effects are visible during the skill animation
        zone_events = [e for e in post_events if e.event_type in ["zone_create", "building_create"]]
        other_events = [e for e in post_events if e.event_type not in ["zone_create", "building_create"]]

        for event in zone_events:
            self.handle_animation_event(event)
        for event in other_events:
            self.handle_animation_event(event)

        self.game_adapter.executing_turn = False

        # Mark grid dirty (terrain may have changed from skills like Marrow Dike)
        self._grid_dirty = True

        # Note: Motor will stop when animations finish (in flush_pending_events or update loop)

        # Fetch messages from game log
        from boneglaive.utils.message_log import message_log
        self.combat_log.add_messages_from_game_log(message_log, count=20)

        # NOTE: DO NOT sync_units_from_game() here!
        # Dead units must remain in visual_units dict until their death animations play
        # They will be removed in the update loop after animations complete

        # In local multiplayer, manually switch players after turn execution
        # (The game engine doesn't do this automatically when local_multiplayer=True)
        if self.game_adapter.game.local_multiplayer:
            old_player = self.game_adapter.game.current_player
            # Toggle between player 1 and 2
            self.game_adapter.game.current_player = 3 - self.game_adapter.game.current_player
            # Increment turn counter when player 1's turn comes around again
            if self.game_adapter.game.current_player == 1:
                self.game_adapter.game.turn += 1

            # Initialize the new player's turn
            self.game_adapter.game.initialize_next_player_turn()

            # Apply player 2 first turn buff (if applicable)
            if self.game_adapter.game.current_player == 2:
                if hasattr(self.game_adapter.game, 'is_player2_first_turn') and self.game_adapter.game.is_player2_first_turn:
                    self._apply_player2_first_turn_buff()
                    self.game_adapter.game.is_player2_first_turn = False

            # Log player switch
            self.combat_log.add_message(f"Player {self.game_adapter.game.current_player}'s turn", "system")

        # Process AI turn if it's player 2's turn and AI is enabled
        # BUT skip if game is already over
        if self.game_adapter.ai_interface and self.game_adapter.game.current_player == 2 and not self.game_adapter.game.winner:
            # Apply player 2 first turn buff (if applicable)
            if hasattr(self.game_adapter.game, 'is_player2_first_turn') and self.game_adapter.game.is_player2_first_turn:
                self._apply_player2_first_turn_buff()
                self.game_adapter.game.is_player2_first_turn = False

            print(f"[AI] Waiting 3 seconds before AI turn...")
            self.combat_log.add_message("AI is thinking...", "system")

            # Wait 3 seconds before AI processes its turn
            # Keep rendering during the wait so the game doesn't freeze
            import time
            start_time = time.time()
            while time.time() - start_time < 3.0:
                delta_time = self.clock.tick(60) / 1000.0
                self.update(delta_time)
                self.draw()
                pygame.display.flip()

            print(f"[AI] Processing AI turn...")

            # Process AI turn (this will set unit actions)
            self.game_adapter.ai_interface.process_turn()

            # Execute the AI's planned actions immediately
            self.execute_turn()

            # Check if AI won - stop processing if game is over
            if self.game_adapter.game.winner:
                print(f"[AI] Game over detected - AI won!")
                return

    def draw_target_pips(self, surface: pygame.Surface):
        """Draw target indicator pips on all tiles that are being targeted."""
        if not self.game_adapter.game:
            return

        game = self.game_adapter.game

        # Count targets for each position
        target_counts = {}  # {(y, x): {'attacks': count, 'skills': count}}

        # Check all units for their targets
        for unit in game.units:
            if unit.hp <= 0:
                continue

            # Check attack targets
            if hasattr(unit, 'attack_target') and unit.attack_target:
                pos = unit.attack_target
                if pos not in target_counts:
                    target_counts[pos] = {'attacks': 0, 'skills': 0}
                target_counts[pos]['attacks'] += 1

            # Check skill targets
            if hasattr(unit, 'skill_target') and unit.skill_target:
                pos = unit.skill_target
                if pos not in target_counts:
                    target_counts[pos] = {'attacks': 0, 'skills': 0}
                target_counts[pos]['skills'] += 1

        # Draw pips for each targeted position
        for (grid_y, grid_x), counts in target_counts.items():
            attack_count = counts['attacks']
            skill_count = counts['skills']

            if attack_count == 0 and skill_count == 0:
                continue

            # Calculate tile position
            tile_x = GRID_OFFSET_X + grid_x * TILE_SIZE
            tile_y = GRID_OFFSET_Y + grid_y * TILE_SIZE

            # Pip settings
            pip_radius = 4
            pip_spacing = 3
            pip_start_x = tile_x + TILE_SIZE - 8
            pip_start_y = tile_y + 8

            # Draw red attack pips
            for i in range(attack_count):
                pip_x = pip_start_x - i * (pip_radius * 2 + pip_spacing)
                pip_y = pip_start_y

                # Main pip - fully opaque
                pygame.draw.circle(surface, (255, 80, 80), (pip_x, pip_y), pip_radius)
                # Highlight - fully opaque
                pygame.draw.circle(surface, (255, 150, 150), (pip_x - 1, pip_y - 1), pip_radius - 2)

            # Draw purple skill pips (below attack pips if any attacks exist)
            for i in range(skill_count):
                pip_x = pip_start_x - i * (pip_radius * 2 + pip_spacing)
                pip_y = pip_start_y + (pip_radius * 2 + pip_spacing) if attack_count > 0 else pip_start_y

                # Main pip - darker purple, fully opaque
                pygame.draw.circle(surface, (140, 80, 200), (pip_x, pip_y), pip_radius)
                # Highlight - fully opaque
                pygame.draw.circle(surface, (180, 120, 230), (pip_x - 1, pip_y - 1), pip_radius - 2)

    def draw_selection_highlight(self, surface: pygame.Surface, unit: AnimatedUnit):
        """Draw highlight around selected unit."""
        # Get unit's grid position
        grid_x = unit.grid_x
        grid_y = unit.grid_y

        # Draw pulsing highlight on the tile
        import math
        import time
        pulse = (math.sin(time.time() * 3) + 1) / 2  # 0 to 1
        alpha = int(100 + pulse * 100)  # 100 to 200

        # Create or reuse cached highlight surface (performance optimization)
        if self._selection_highlight_cache is None or self._last_selection_alpha != alpha:
            self._selection_highlight_cache = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            self._selection_highlight_cache.fill((0, 0, 0, 0))  # Clear
            pygame.draw.rect(self._selection_highlight_cache, (*COLOR_SELECTION, alpha),
                           self._selection_highlight_cache.get_rect())
            # Draw border
            border_color = (*COLOR_SELECTION, 255)
            pygame.draw.rect(self._selection_highlight_cache, border_color,
                           self._selection_highlight_cache.get_rect(), 3)
            self._last_selection_alpha = alpha

        highlight_surf = self._selection_highlight_cache

        # Position on grid (current position)
        tile_x = GRID_OFFSET_X + grid_x * TILE_SIZE
        tile_y = GRID_OFFSET_Y + grid_y * TILE_SIZE
        surface.blit(highlight_surf, (tile_x, tile_y))

        # If unit has a pending move, also highlight the ghost position
        game_unit = self._get_game_unit(unit)
        if game_unit and hasattr(game_unit, 'move_target') and game_unit.move_target:
            ghost_y, ghost_x = game_unit.move_target
            ghost_tile_x = GRID_OFFSET_X + ghost_x * TILE_SIZE
            ghost_tile_y = GRID_OFFSET_Y + ghost_y * TILE_SIZE
            surface.blit(highlight_surf, (ghost_tile_x, ghost_tile_y))

    def draw_astral_values(self, surface: pygame.Surface):
        """Draw pulsating golden astral values over furniture when DELPHIC APPRAISER is selected."""
        if not self.game_adapter.game or not self.game_adapter.game.map:
            return

        game_map = self.game_adapter.game.map
        current_player = self.game_adapter.game.current_player

        # Calculate pulse effect (slower, more elegant)
        import math
        pulse = (math.sin(self.astral_value_pulse_time * 2) + 1) / 2  # 0 to 1
        alpha = int(120 + pulse * 135)  # 120 to 255 (more transparent to fully opaque)
        scale = 1.0 + pulse * 0.2  # 1.0 to 1.2x scale

        # Scan all furniture on map
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if game_map.is_furniture(y, x):
                    # Get astral value for current player
                    astral_value = game_map.get_cosmic_value(y, x, current_player, self.game_adapter.game)

                    if astral_value is not None:
                        # Calculate screen position (center of tile)
                        tile_x = GRID_OFFSET_X + x * TILE_SIZE + TILE_SIZE // 2
                        tile_y = GRID_OFFSET_Y + y * TILE_SIZE + TILE_SIZE // 2

                        # Render number with gold color and transparency
                        font_size = int(48 * scale)  # Large number, scales with pulse

                        # PERFORMANCE FIX: Use cached fonts instead of creating new ones
                        # Get or create main font
                        if font_size not in self._astral_value_font_cache:
                            self._astral_value_font_cache[font_size] = pygame.font.Font(None, font_size)
                        value_font = self._astral_value_font_cache[font_size]

                        # Get or create outline font
                        outline_size = font_size + 2
                        if outline_size not in self._astral_value_font_cache:
                            self._astral_value_font_cache[outline_size] = pygame.font.Font(None, outline_size)
                        outline_font = self._astral_value_font_cache[outline_size]

                        # Render the number
                        value_text = value_font.render(str(astral_value), True, (255, 215, 0))  # Gold

                        # Apply transparency
                        value_text.set_alpha(alpha)

                        # Center the text on the tile
                        text_rect = value_text.get_rect(center=(tile_x, tile_y))

                        # Add dark outline for readability
                        outline_text = outline_font.render(str(astral_value), True, (0, 0, 0))
                        outline_text.set_alpha(alpha // 2)
                        outline_rect = outline_text.get_rect(center=(tile_x, tile_y))
                        surface.blit(outline_text, outline_rect)

                        # Draw the main golden number
                        surface.blit(value_text, text_rect)

    def draw_skill_shadows(self, surface: pygame.Surface):
        """Draw semi-transparent ghost indicators of units at skill target indicator positions."""
        if not self.game_adapter.game:
            return

        import time

        # Pulse effect for wispy shadows (slower, more ethereal)
        pulse_time = time.time()
        pulse = (math.sin(pulse_time * 1.5) + 1) / 2  # 0 to 1, slower oscillation
        base_alpha = int(140 + pulse * 60)  # 140 to 200 alpha (55-78% opacity)

        # Check all units for skill target indicators
        for unit in self.units:
            if not unit or unit.hp <= 0:
                continue

            # Get corresponding game unit to check for indicators
            game_unit = self._get_game_unit(unit)
            if not game_unit:
                continue

            shadow_positions = []  # List of (grid_y, grid_x) positions to draw shadows

            # Check for basic movement target (set when clicking to move)
            if hasattr(game_unit, 'move_target') and game_unit.move_target:
                shadow_positions.append(game_unit.move_target)

            # Check for vault target indicator (GLAIVEMAN Vault)
            if hasattr(game_unit, 'vault_target_indicator') and game_unit.vault_target_indicator:
                shadow_positions.append(game_unit.vault_target_indicator)

            # Check for teleport target indicator (GRAYMAN Teleport, Delta Config, Grae Exchange)
            if hasattr(game_unit, 'teleport_target_indicator') and game_unit.teleport_target_indicator:
                shadow_positions.append(game_unit.teleport_target_indicator)

            # Check for Market Futures indicator (DELPHIC APPRAISER)
            if hasattr(game_unit, 'market_futures_indicator') and game_unit.market_futures_indicator:
                shadow_positions.append(game_unit.market_futures_indicator)

            # Check for Divine Depreciation indicator (DELPHIC APPRAISER)
            if hasattr(game_unit, 'divine_depreciation_indicator') and game_unit.divine_depreciation_indicator:
                shadow_positions.append(game_unit.divine_depreciation_indicator)

            # Check for Broaching Gas indicator (GAS MACHINIST)
            if hasattr(game_unit, 'broaching_gas_indicator') and game_unit.broaching_gas_indicator:
                shadow_positions.append(game_unit.broaching_gas_indicator)

            # Check for Saft-E-Gas indicator (GAS MACHINIST)
            if hasattr(game_unit, 'saft_e_gas_indicator') and game_unit.saft_e_gas_indicator:
                shadow_positions.append(game_unit.saft_e_gas_indicator)

            # Gaussian Dusk charging indicator no longer exists (fires immediately)

            # Special handling for Expedite path indicator (GRAYMAN - shows movement path)
            if hasattr(game_unit, 'expedite_path_indicator') and game_unit.expedite_path_indicator:
                # Only show shadow at the final destination
                if isinstance(game_unit.expedite_path_indicator, list) and len(game_unit.expedite_path_indicator) > 0:
                    final_pos = game_unit.expedite_path_indicator[-1]  # Last position in path
                    shadow_positions.append(final_pos)

            # Note: Other special indicators not included (they show areas, not unit destination):
            # - site_inspection_indicator (shows 3x3 area for inspection)
            # - jawline_indicator (shows network area)
            # - parabol_indicator (shows area)
            # - fragcrest_indicator (shows cone)
            # - auction_curse_ally_indicator, auction_curse_enemy_indicator (not movement targets)

            # Draw shadow at each indicator position
            for pos in shadow_positions:
                grid_y, grid_x = pos

                # Convert grid position to screen coordinates (center of tile)
                shadow_x = GRID_OFFSET_X + grid_x * TILE_SIZE + TILE_SIZE // 2
                shadow_y = GRID_OFFSET_Y + grid_y * TILE_SIZE + TILE_SIZE // 2

                # Create shadow surface
                if unit.sprite:
                    # Use actual sprite with transparency
                    shadow_sprite = unit.sprite.copy()

                    # Apply tint for wispy effect (brighter blue tint)
                    tint_surface = pygame.Surface(shadow_sprite.get_size(), pygame.SRCALPHA)
                    tint_color = (150, 200, 255, 80)  # Brighter blue tint, more prominent
                    tint_surface.fill(tint_color)
                    shadow_sprite.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

                    # Apply transparency
                    shadow_sprite.set_alpha(base_alpha)

                    # Draw shadow centered at position
                    shadow_rect = shadow_sprite.get_rect(center=(shadow_x, shadow_y))
                    surface.blit(shadow_sprite, shadow_rect)
                else:
                    # Fallback: draw semi-transparent circle
                    shadow_color = (*unit.color[:3], base_alpha)
                    shadow_surface = pygame.Surface((unit.radius * 2, unit.radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surface, shadow_color,
                                     (unit.radius, unit.radius), unit.radius)
                    # Add wispy outer glow
                    glow_color = (200, 220, 255, base_alpha // 3)
                    pygame.draw.circle(shadow_surface, glow_color,
                                     (unit.radius, unit.radius), unit.radius + 4)
                    surface.blit(shadow_surface,
                               (shadow_x - unit.radius, shadow_y - unit.radius))

    def draw_imbued_furniture(self, surface: pygame.Surface):
        """Draw glowing currency symbol and gold sparkles on furniture imbued by Market Futures."""
        if not self.game_adapter.game:
            return

        game = self.game_adapter.game

        # Check if there are any teleport anchors (Market Futures)
        if not hasattr(game, 'teleport_anchors') or not game.teleport_anchors:
            return

        import math
        import random

        # Calculate wave effect for currency symbol
        alpha = int(140 + math.sin(self.astral_value_pulse_time * 2.5) * 60)  # 80 to 200
        wave_offset = math.sin(self.astral_value_pulse_time * 3) * 8  # Vertical wave amplitude

        # Iterate through all teleport anchors
        for anchor_pos, anchor_data in game.teleport_anchors.items():
            # Only draw if furniture is still imbued
            if not anchor_data.get('imbued', False):
                continue

            grid_y, grid_x = anchor_pos

            # Calculate screen position (center of tile)
            tile_x = GRID_OFFSET_X + grid_x * TILE_SIZE + TILE_SIZE // 2
            tile_y = GRID_OFFSET_Y + grid_y * TILE_SIZE + TILE_SIZE // 2

            # Draw waving currency symbol (¤) - 200% larger = 120pt (was 40pt)
            font_size = 120
            currency_font = pygame.font.Font(None, font_size)
            currency_text = currency_font.render("¤", True, (255, 215, 0))  # Gold
            currency_text.set_alpha(alpha)

            # Apply wave offset to y position for undulating effect
            wave_y = tile_y + wave_offset

            # Center the symbol with wave offset
            text_rect = currency_text.get_rect(center=(tile_x, int(wave_y)))

            # Draw dark outline for visibility
            outline_font = pygame.font.Font(None, font_size + 2)
            outline_text = outline_font.render("¤", True, (0, 0, 0))
            outline_text.set_alpha(alpha // 2)
            outline_rect = outline_text.get_rect(center=(tile_x, int(wave_y)))
            surface.blit(outline_text, outline_rect)

            # Draw main currency symbol
            surface.blit(currency_text, text_rect)

            # Spawn new sparkles (1 every few frames on average)
            # Use probability instead of guaranteed spawns
            if random.random() < 0.3:  # 30% chance per frame = ~18 sparkles/sec at 60fps
                spawn_count = 1
            else:
                spawn_count = 0
            for _ in range(spawn_count):
                # Random position within tile bounds
                spawn_x = tile_x + random.uniform(-TILE_SIZE // 3, TILE_SIZE // 3)
                spawn_y = tile_y + random.uniform(-TILE_SIZE // 3, TILE_SIZE // 3)

                # Random velocity (upward with slight horizontal drift)
                vx = random.uniform(-10, 10)  # Horizontal drift
                vy = random.uniform(-40, -60)  # Upward speed (negative = up)

                # Random properties
                max_life = random.uniform(1.0, 1.5)  # Lifetime in seconds
                size = random.randint(2, 4)
                color = random.choice([(255, 235, 100), (255, 215, 0)])  # Bright gold or gold

                self.imbued_sparkles.append({
                    'x': spawn_x,
                    'y': spawn_y,
                    'vx': vx,
                    'vy': vy,
                    'life': 0,  # Current age
                    'max_life': max_life,
                    'size': size,
                    'color': color
                })

        # Draw all active sparkles
        for sparkle in self.imbued_sparkles:
            # Calculate fade based on life
            life_ratio = sparkle['life'] / sparkle['max_life']
            sparkle_alpha = int(220 * (1.0 - life_ratio))  # Fade from 220 to 0

            if sparkle_alpha > 0:
                # Performance: Get or create cached sparkle surface for this size
                size = sparkle['size']
                cache_key = size * 2  # Surface size
                if cache_key not in self._sparkle_surf_cache:
                    self._sparkle_surf_cache[cache_key] = pygame.Surface((cache_key, cache_key), pygame.SRCALPHA)

                sparkle_surf = self._sparkle_surf_cache[cache_key]
                sparkle_surf.fill((0, 0, 0, 0))  # Clear surface
                pygame.draw.circle(
                    sparkle_surf,
                    (*sparkle['color'], sparkle_alpha),
                    (size, size),
                    size
                )
                surface.blit(sparkle_surf, (int(sparkle['x'] - size), int(sparkle['y'] - size)))

    def start_respawn_mode(self):
        """Start respawn mode - show list of ready-to-respawn units."""
        if not self.game_adapter.game:
            return

        current_player = self.game_adapter.game.current_player

        # Get ready-to-respawn dead units for current player
        ready_dead_units = [du for du in self.game_adapter.game.dead_units
                           if du.player == current_player and du.ready_for_respawn]

        if not ready_dead_units:
            self.combat_log.add_message("No units ready to respawn", "system")
            return

        # Enter respawn unit selection mode
        self.respawn_mode = True
        self.respawn_selecting_unit = True
        self.respawn_selecting_location = False
        self.current_action_mode = "RESPAWN"

        # Show respawn window
        self.respawn_window.show(ready_dead_units)

        self.combat_log.add_message(f"Select unit to respawn ({len(ready_dead_units)} available)", "system")
        print(f"[Respawn] Showing {len(ready_dead_units)} units ready for respawn")

    def confirm_respawn_unit_selection(self):
        """Confirm unit selection and enter location selection mode."""
        if not self.respawn_selecting_unit:
            return

        selected_unit = self.respawn_window.get_selected_unit()
        if not selected_unit:
            return

        # Set selected dead unit and enter location selection mode
        self.selected_dead_unit = selected_unit
        self.respawn_selecting_unit = False
        self.respawn_selecting_location = True

        # Hide respawn window
        self.respawn_window.hide()

        # Get valid respawn tiles
        if self.game_adapter.game:
            valid_tiles = self.game_adapter.game.get_valid_respawn_tiles(
                self.game_adapter.game.current_player
            )
            self.respawn_valid_tiles = valid_tiles
            print(f"[Respawn] {len(valid_tiles)} valid spawn locations")

        self.combat_log.add_message(
            f"Select respawn location for {selected_unit.greek_id}",
            "system"
        )

    def confirm_respawn_location(self):
        """Confirm respawn at current ghost position."""
        if not self.respawn_selecting_location or not self.selected_dead_unit:
            return

        if not self.respawn_ghost_pos:
            self.combat_log.add_message("No location selected", "system")
            return

        pos = (self.respawn_ghost_pos[1], self.respawn_ghost_pos[0])  # Convert to (y, x)

        # Check if position is valid
        if pos not in self.respawn_valid_tiles:
            self.combat_log.add_message("Invalid respawn location", "system")
            return

        # Queue the respawn
        success = self.game_adapter.game.queue_respawn(self.selected_dead_unit, pos)

        if success:
            self.combat_log.add_message(
                f"{self.selected_dead_unit.greek_id} respawn queued at {pos}",
                "system"
            )
            self.exit_respawn_mode()
        else:
            self.combat_log.add_message("Invalid respawn location (blocked or occupied)", "system")

    def exit_respawn_mode(self):
        """Exit respawn mode."""
        self.respawn_mode = False
        self.respawn_selecting_unit = False
        self.respawn_selecting_location = False
        self.selected_dead_unit = None
        self.respawn_valid_tiles = []
        self.respawn_ghost_pos = None
        self.current_action_mode = "SELECT"

        # Hide respawn window
        self.respawn_window.hide()

        print("[Respawn] Exited respawn mode")

    def show_game_over_window(self):
        """Show the game over window when a player wins."""
        if not self.game_adapter.game or not self.game_adapter.game.winner:
            return

        game = self.game_adapter.game
        winner = game.winner
        loser = 2 if winner == 1 else 1

        winner_name = game.get_player_name(winner)
        loser_name = game.get_player_name(loser)
        winner_gp = game.player1_gp if winner == 1 else game.player2_gp
        loser_gp = game.player2_gp if winner == 1 else game.player1_gp

        # Determine if local player won (in single player, player 1 is local)
        # In multiplayer, this would need adjustment based on network mode
        is_victory = (winner == 1)

        self.game_over_window.show(is_victory, winner_name, winner_gp, loser_name, loser_gp, winner_player=winner)
        print(f"[Game Over] {winner_name} wins with {winner_gp} GP!")

    def return_to_main_menu(self):
        """Return to the main menu."""
        print("[Game Over] Returning to main menu...")

        # Close the game over window
        self.game_over_window.hide()

        # Set flag to return to menu
        self.return_to_menu = True

        # Stop the renderer loop
        self.running = False

    def confirm_concede(self):
        """Handle confirmed concession - opponent wins."""
        if not self.game_adapter.game:
            return

        print("[Concede] Player conceding...")

        # Hide the concede dialog
        self.concede_dialog.hide()

        # Get current player
        current_player = self.game_adapter.game.current_player

        # Concede the game (opponent wins)
        self.game_adapter.game.concede(current_player)

        # Add combat log message
        self.combat_log.add_message(f"Player {current_player} has conceded.", "system")

        # Show game over window
        self.show_game_over_window()

    def start_setup_mode(self):
        """Start setup mode - show unit selection window."""
        if not self.game_adapter.game:
            return

        current_player = self.game_adapter.game.setup_player
        units_remaining = self.game_adapter.game.setup_units_remaining[current_player]

        # Count how many of each type already placed
        unit_counts = {}
        from boneglaive.utils.constants import UnitType
        for unit_type in UnitType:
            unit_counts[unit_type] = self.game_adapter.game.count_player_units_by_type(current_player, unit_type)

        # Enter setup unit selection mode
        self.setup_mode = True
        self.setup_selecting_unit = True
        self.setup_placing_unit = False
        self.current_action_mode = "SETUP"

        # Show setup window
        self.setup_window.show(current_player, units_remaining, unit_counts)

        # Initialize help panel with first unit
        display_unit = self.setup_window.get_display_unit()
        self.setup_unit_help.update(display_unit)

        self.combat_log.add_message(f"Player {current_player}, select and place your units!", "system")
        print(f"[Setup] Player {current_player} setup mode started - {units_remaining} units remaining")

    def confirm_unit_type_selection(self):
        """Confirm unit type selection and enter placement mode."""
        if not self.setup_selecting_unit:
            return

        selected_type = self.setup_window.get_selected_unit_type()
        if not selected_type:
            return

        # Get display name for unit type (handles both enums and integers)
        unit_display_name = self.setup_window.unit_names.get(selected_type, str(selected_type))

        # Check if this type is already maxed out (2 of same type limit)
        if self.setup_window.is_unit_type_maxed(selected_type):
            self.combat_log.add_message(f"Cannot place more than 2 {unit_display_name} units", "system")
            return

        # Set selected type and enter placement mode
        self.selected_unit_type = selected_type
        self.setup_selecting_unit = False
        self.setup_placing_unit = True

        # Get valid placement tiles
        if self.game_adapter.game:
            # All tiles that can have units placed are valid
            valid_tiles = []
            for y in range(self.game_adapter.game.map.height):
                for x in range(self.game_adapter.game.map.width):
                    if (self.game_adapter.game.map.can_place_unit(y, x) and
                        self.game_adapter.game.is_valid_position(y, x)):
                        valid_tiles.append((y, x))
            self.setup_valid_tiles = valid_tiles
            print(f"[Setup] {len(valid_tiles)} valid placement tiles")

        # Hide setup window
        self.setup_window.hide()

        self.combat_log.add_message(
            f"Place {unit_display_name} unit on the map (ESC to go back)",
            "system"
        )

    def confirm_unit_placement(self):
        """Confirm unit placement at current cursor position."""
        if not self.setup_placing_unit or not self.selected_unit_type:
            return

        if not self.setup_ghost_pos:
            self.combat_log.add_message("No location selected", "system")
            return

        grid_x, grid_y = self.setup_ghost_pos  # screen_to_grid returns (grid_x, grid_y)

        # Convert to game logic coordinates (y, x)
        y, x = grid_y, grid_x

        # Check if position is valid
        pos_tuple = (y, x)
        if pos_tuple not in self.setup_valid_tiles:
            self.combat_log.add_message("Invalid placement location", "system")
            return

        # Place the unit
        result = self.game_adapter.game.place_setup_unit(y, x, self.selected_unit_type)

        if result is True:
            # Success! Sync the new unit
            self.sync_units_from_game()

            current_player = self.game_adapter.game.setup_player
            units_remaining = self.game_adapter.game.setup_units_remaining[current_player]

            # Get display name (handles both enums and integers)
            unit_display_name = self.setup_window.unit_names.get(self.selected_unit_type, str(self.selected_unit_type))
            self.combat_log.add_message(
                f"{unit_display_name} placed! {units_remaining} remaining",
                "system"
            )

            # Check if all units placed
            if units_remaining == 0:
                # Return to unit selection to show confirm button
                self.return_to_unit_selection()
            else:
                # Return to unit selection for next placement
                self.return_to_unit_selection()

        elif result == "max_unit_type_limit":
            # Get display name (handles both enums and integers)
            unit_display_name = self.setup_window.unit_names.get(self.selected_unit_type, str(self.selected_unit_type))
            self.combat_log.add_message(f"Cannot place more than 2 {unit_display_name} units", "system")
        elif result == "position_occupied":
            self.combat_log.add_message("Position occupied by your unit", "system")
        else:
            self.combat_log.add_message("Invalid placement location", "system")

    def return_to_unit_selection(self):
        """Return from placement mode to unit selection."""
        self.setup_placing_unit = False
        self.setup_selecting_unit = True
        self.selected_unit_type = None
        self.setup_ghost_pos = None
        self.setup_valid_tiles = []

        # Update and re-show setup window
        current_player = self.game_adapter.game.setup_player
        units_remaining = self.game_adapter.game.setup_units_remaining[current_player]

        # Count how many of each type already placed
        unit_counts = {}
        from boneglaive.utils.constants import UnitType
        for unit_type in UnitType:
            unit_counts[unit_type] = self.game_adapter.game.count_player_units_by_type(current_player, unit_type)

        self.setup_window.update_state(units_remaining, unit_counts)
        self.setup_window.visible = True

    def confirm_setup_complete(self):
        """Confirm setup is complete and proceed to next phase."""
        if not self.setup_mode:
            return

        current_player = self.game_adapter.game.setup_player
        units_remaining = self.game_adapter.game.setup_units_remaining[current_player]

        # Make sure all units have been placed
        if units_remaining > 0:
            self.combat_log.add_message(f"Place all {units_remaining} units before confirming", "system")
            return

        # Confirm setup with game engine
        game_start = self.game_adapter.game.confirm_setup()

        if game_start:
            # Game is starting! Exit setup mode
            self.exit_setup_mode()
            self.combat_log.add_message("Setup complete! Game starting...", "system")
            self.combat_log.add_message(f"Player {self.game_adapter.game.current_player}'s turn", "system")

            # Sync units now that setup is complete
            self.sync_units_from_game()
        else:
            # Player 2's turn to set up (local multiplayer)
            self.exit_setup_mode()
            self.start_setup_mode()  # Start setup for player 2

    def exit_setup_mode(self):
        """Exit setup mode."""
        self.setup_mode = False
        self.setup_selecting_unit = False
        self.setup_placing_unit = False
        self.selected_unit_type = None
        self.setup_valid_tiles = []
        self.setup_ghost_pos = None
        self.current_action_mode = "SELECT"

        # Hide setup window
        self.setup_window.hide()

        # Force sync all animated unit positions with game units
        # This is critical for FOWL_CONTRIVANCE which gets snapped to rails after setup
        if self.game_adapter.game:
            from boneglaive.graphical.animations.core import TILE_SIZE
            for animated_unit in self.units:
                # Use the direct game_unit reference stored in AnimatedUnit
                # This avoids the bug where multiple units of the same type would all match the first one
                game_unit = animated_unit.game_unit

                if game_unit:
                    # Update grid coordinates
                    animated_unit.grid_x = game_unit.x
                    animated_unit.grid_y = game_unit.y

                    # Calculate and set screen coordinates
                    new_x = game_unit.x * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
                    new_y = game_unit.y * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y

                    # Set both current and target position (no animation)
                    animated_unit.x = new_x
                    animated_unit.y = new_y
                    animated_unit.target_x = new_x
                    animated_unit.target_y = new_y
                    animated_unit.is_moving = False

        print("[Setup] Exited setup mode")

    def _handle_cursor_movement(self, key):
        """Handle cursor movement during setup placement."""
        if not self.setup_ghost_pos:
            # Start at center of map
            self.setup_ghost_pos = (5, 10)
            return

        y, x = self.setup_ghost_pos

        if key == pygame.K_UP:
            y = max(0, y - 1)
        elif key == pygame.K_DOWN:
            y = min(self.game_adapter.game.map.height - 1, y + 1)
        elif key == pygame.K_LEFT:
            x = max(0, x - 1)
        elif key == pygame.K_RIGHT:
            x = min(self.game_adapter.game.map.width - 1, x + 1)

        self.setup_ghost_pos = (y, x)

    def run(self):
        """Main game loop."""
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0  # Convert to seconds

            # Update FPS counter
            if self.show_fps:
                current_fps = self.clock.get_fps()
                self.fps_values.append(current_fps)
                # Keep only last 30 frames for smoothing
                if len(self.fps_values) > 30:
                    self.fps_values.pop(0)
                # Calculate average FPS
                if len(self.fps_values) > 0:
                    self.fps_display = sum(self.fps_values) / len(self.fps_values)

            self.handle_events()
            self.update(delta_time)
            self.draw()

        # Only quit pygame if NOT returning to menu
        if not self.return_to_menu:
            pygame.quit()


def main():
    """Entry point for graphical version."""
    # Load config to get selected map and network mode
    from boneglaive.utils.config import ConfigManager
    config = ConfigManager()
    selected_map = config.get('selected_map', 'hard_pressed')
    network_mode = config.get('network_mode', 'single')

    # Create game state adapter
    adapter = GameStateAdapter()

    # Create renderer first (needed for AI animations)
    renderer = GraphicalRenderer(adapter)

    # Create UI adapter for AI animations
    from boneglaive.graphical.ui_adapter import GraphicalUIAdapter
    ui_adapter = GraphicalUIAdapter(renderer)

    # Initialize game with real game logic
    print("Initializing game...")
    print(f"Network mode: {network_mode}")
    # skip_setup=False means game starts in setup phase
    adapter.initialize_game(skip_setup=False, map_name=selected_map, network_mode=network_mode, ui_adapter=ui_adapter)
    print(f"Game created - starting in setup phase on map: {selected_map}")

    # Set up terrain change callback so renderer marks tiles dirty when terrain changes
    if adapter.game and adapter.game.map:
        adapter.game.map.terrain_change_callback = renderer.mark_tile_dirty
        print("Terrain change callback registered")

    # Sync units from game
    print("Syncing units from game to renderer...")
    renderer.sync_units_from_game()
    print(f"Created {len(renderer.units)} visual units")

    # Add welcome messages to combat log
    renderer.combat_log.add_message("Welcome to Boneglaive!", "system")
    renderer.combat_log.add_message(f"Player {adapter.game.current_player}'s turn", "system")

    # Run game loop
    renderer.run()


if __name__ == "__main__":
    main()
