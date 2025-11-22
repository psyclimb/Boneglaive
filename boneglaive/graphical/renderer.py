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
from .ui.skill_bar import SkillBar
from .ui.combat_log import CombatLog
from .ui.status_effects import StatusEffectsPanel
from .ui.unit_info import UnitInfoPanel
from .ui_adapter import GraphicalUIAdapter


# Screen constants
SCREEN_WIDTH = 1480  # Increased to fit 20-column grid (20*64 + 100 offset + margin)
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Boneglaive"

# Grid constants - Match game map size (20 cols x 10 rows)
GRID_WIDTH = 20
GRID_HEIGHT = 10
GRID_OFFSET_X = 100  # Offset to leave room for UI panels
GRID_OFFSET_Y = 50

# Colors
COLOR_BG = (40, 44, 52)
COLOR_GRID_DARK = (50, 54, 62)
COLOR_GRID_LIGHT = (60, 64, 72)
COLOR_SELECTION = (100, 200, 255)
COLOR_TARGET = (255, 100, 100)
COLOR_MOVEMENT = (100, 255, 100)


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

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.large_font = pygame.font.Font(None, 36)

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
        self.valid_positions: List[Tuple[int, int]] = []
        self.attack_positions: List[Tuple[int, int]] = []
        self.skill_positions: List[Tuple[int, int]] = []
        self.selected_skill = None

        # UI Components
        self.skill_bar = SkillBar(self.font, self.small_font)
        self.combat_log = CombatLog(self.small_font)
        self.status_effects_panel = StatusEffectsPanel(self.font, self.small_font)
        self.unit_info_panel = UnitInfoPanel(self.font, self.small_font, self.large_font)

        # UI Adapter for animations
        self.ui_adapter = GraphicalUIAdapter(self)

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
            unit_type: UnitType enum

        Returns:
            Path to sprite file
        """
        # Map unit types to sprite filenames
        unit_type_name = str(unit_type).split('.')[-1].lower()
        sprite_path = f"graphics/units/{unit_type_name}.svg"
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
            sprite_path=sprite_path
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

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_t:
                    # End turn (changed from E to avoid conflict with skill hotkeys)
                    self.execute_turn()
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                  pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r]:
                    # Handle skill hotkeys
                    skill = self.skill_bar.handle_hotkey(event.key)
                    if skill and self.selected_unit:
                        print(f"Skill selected: {skill.name}")
                        self.selected_skill = skill

                        # Query skill range
                        game_unit = self._get_game_unit(self.selected_unit)
                        if game_unit:
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
                # Update hovered grid position
                self.hovered_grid_pos = self.screen_to_grid(event.pos[0], event.pos[1])

                # Update skill bar hover
                self.skill_bar.handle_mouse_motion(event.pos)

                # Update status effects hover (for tooltips)
                self.status_effects_panel.handle_mouse_motion(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    grid_pos = self.screen_to_grid(event.pos[0], event.pos[1])
                    if grid_pos:
                        self.handle_grid_click(grid_pos[0], grid_pos[1])

                elif event.button == 3:  # Right click
                    # Cancel selection and skill mode
                    self.selected_unit = None
                    self.selected_skill = None
                    self.show_movement_range = False
                    self.show_target_range = False
                    self.show_skill_range = False
                    self.valid_positions = []
                    self.attack_positions = []
                    self.skill_positions = []
                    self.skill_bar.update(None, None)
                    self.status_effects_panel.update(None)
                    self.unit_info_panel.update(None, None)

    def handle_grid_click(self, grid_x: int, grid_y: int):
        """
        Handle click on grid tile.

        Args:
            grid_x, grid_y: Grid coordinates clicked
        """
        unit = self.get_unit_at_grid(grid_x, grid_y)

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
                    # Use the skill
                    target_pos = (grid_y, grid_x)  # Convert to game coords
                    # Plan the skill use (don't execute yet - wait for turn execution)
                    game_unit.skill_target = target_pos
                    game_unit.selected_skill = self.selected_skill  # Store the skill object, not name
                    game_unit.took_no_actions = False

                    # Track action order
                    game_unit.action_timestamp = self.game_adapter.game.action_counter
                    self.game_adapter.game.action_counter += 1

                    print(f"Skill planned: {self.selected_skill.name} at ({grid_y}, {grid_x})")

                    # Clear skill targeting mode
                    self.selected_skill = None
                    self.show_skill_range = False
                    self.skill_positions = []

                    # Restore normal range display
                    if game_unit:
                        self.valid_positions = self.game_adapter.get_movement_range(game_unit)
                        self.attack_positions = self.game_adapter.get_attack_range(game_unit)
                        self.show_movement_range = True
                        self.show_target_range = True
                    else:
                        print(f"Failed to use skill")
            else:
                print(f"Target out of skill range")
            return  # Don't process normal click logic when in skill mode

        # Unit selection
        if unit:
            # Check if this is a friendly unit (current player's unit)
            if unit.player == current_player:
                # Select friendly unit
                self.selected_unit = unit
                self.show_movement_range = True
                self.show_target_range = True

                # Query movement range and attack range from game logic
                game_unit = self._get_game_unit(unit)
                if game_unit:
                    self.valid_positions = self.game_adapter.get_movement_range(game_unit)
                    self.attack_positions = self.game_adapter.get_attack_range(game_unit)

                    # Update skill bar, status effects, and unit info
                    self.skill_bar.update(unit, game_unit)
                    self.status_effects_panel.update(game_unit)
                    self.unit_info_panel.update(unit, game_unit)

                    print(f"Selected: {unit.name} - {len(self.valid_positions)} moves, {len(self.attack_positions)} attacks available")
                else:
                    self.valid_positions = []
                    self.attack_positions = []
                    self.skill_bar.update(None, None)
                    self.status_effects_panel.update(None)
                    self.unit_info_panel.update(None, None)
                    print(f"Selected: {unit.name} - WARNING: No game unit found")
            else:
                # Clicked enemy - attack if we have unit selected
                if self.selected_unit:
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
                            self.valid_positions = []
                            self.attack_positions = []
                            self.skill_bar.update(None, None)
                            self.status_effects_panel.update(None)
                            self.unit_info_panel.update(None, None)
                    else:
                        print(f"Enemy {unit.name} out of attack range")
                else:
                    # Clicked enemy with no unit selected - just show info
                    game_unit = self._get_game_unit(unit)
                    if game_unit:
                        # Update status effects panel and unit info to show enemy info
                        self.status_effects_panel.update(game_unit)
                        self.unit_info_panel.update(unit, game_unit)
                        print(f"Enemy unit: {unit.name} (Player {unit.player})")
                    else:
                        self.status_effects_panel.update(None)
                        self.unit_info_panel.update(None, None)
                        print(f"Enemy unit: {unit.name} (Player {unit.player}) - WARNING: No game unit found")
        else:
            # Clicked empty tile
            if self.selected_unit:
                # Check if clicked position is in movement range
                if (grid_x, grid_y) in self.valid_positions:
                    # Execute movement
                    game_unit = self._get_game_unit(self.selected_unit)
                    if game_unit:
                        # Set move target (game uses y, x coordinates)
                        game_unit.move_target = (grid_y, grid_x)
                        game_unit.took_no_actions = False

                        # Track action order
                        game_unit.action_timestamp = self.game_adapter.game.action_counter
                        self.game_adapter.game.action_counter += 1

                        print(f"Move planned: {self.selected_unit.name} → ({grid_x}, {grid_y})")

                        # Clear selection and movement range
                        self.selected_unit = None
                        self.show_movement_range = False
                        self.valid_positions = []
                    else:
                        print(f"ERROR: Could not find game unit for {self.selected_unit.name}")
                else:
                    print(f"Cannot move there - not in movement range")
                    # Could add visual feedback here (red flash, etc.)

    def _get_unit_id(self, unit) -> Optional[str]:
        """Helper to get unit ID."""
        if not unit:
            return None
        return unit.name  # TODO: Use proper unit ID

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

    def flush_pending_events(self):
        """Show all pending damage/heal numbers after animations complete."""
        for event in self.pending_animation_events:
            self._show_event_immediately(event)
        self.pending_animation_events = []

        # After flushing damage/skill events, check all units for active status effects
        # and show icons for any that are currently active
        self._show_active_status_effects()

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

    def update(self, delta_time: float):
        """
        Update game state and animations.

        Args:
            delta_time: Time since last frame in seconds
        """
        if self.paused:
            return

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
        animation_events = self.game_adapter.sync_state()
        for event in animation_events:
            self.handle_animation_event(event)

        # Update units
        for unit in self.units:
            unit.update(delta_time)

        # Update particles
        self.particle_emitter.update(delta_time)
        self.floating_texts = [t for t in self.floating_texts if t.update(delta_time)]

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

            if still_active:
                updated_animations.append(anim)

        self.active_animations = updated_animations

        # Check if all animations finished - if so, flush pending damage/heal/death events
        if self.pending_animation_events and not self.has_active_animations():
            self.flush_pending_events()

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
        if event.event_type == "damage" or event.event_type == "heal" or event.event_type == "geas_heal" or event.event_type == "scalar_trap":
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

        elif event.event_type == "status_effect":
            # Status effects are now handled via callback and shown after damage numbers
            # This event type is no longer used
            print(f"  [Renderer] WARNING: Received deprecated status_effect event")

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
            unit_type_name = attacker.type.name if attacker.type else "None"
            print(f"  [DEBUG] Attacker unit type: {unit_type_name}")
            if attacker.type == UnitType.INTERFERER and attack_target:
                print(f"  [Renderer] *** INTERFERER ATTACK DETECTED ***")

                # Check if this attack has carrier_rave flag (captured from game state BEFORE execution cleared it)
                has_carrier_rave = event.kwargs.get("has_carrier_rave", False)
                if has_carrier_rave:
                    print(f"  [Renderer] *** CARRIER RAVE FLAG DETECTED - using triple strike animation ***")

                from boneglaive.graphical.animations.animation_factory import AnimationFactory

                if has_carrier_rave:
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
                        screen_flash_callback=self.trigger_screen_flash
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
                        screen_flash_callback=self.trigger_screen_flash
                    )

                    if neutron_animation:
                        self.active_animations.append(neutron_animation)
                        print(f"  [Animation] *** Successfully triggered Neutron Illuminant flash - added to active_animations (count: {len(self.active_animations)}) ***")
                    else:
                        print(f"  [Animation] WARNING: Failed to create Neutron Illuminant animation")
            else:
                print(f"  [DEBUG] Not INTERFERER or no attack target")

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
        target_game_unit = None
        if skill_target:
            target_grid_x = skill_target[1]  # Convert (y,x) to (x,y)
            target_grid_y = skill_target[0]
            target_unit = self._get_unit_at_grid(target_grid_x, target_grid_y)
            # NOTE: target_pos is in (grid_y, grid_x) format to match caster_grid_pos format in animations
            target_pos = (target_grid_y, target_grid_x)
            # Get game unit for crit check
            target_game_unit = self.game_adapter.game.get_unit_at(skill_target[0], skill_target[1])

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

        # Create animation via factory
        print(f"  [Renderer] Creating animation for {skill_name}...")
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
            units_list=self.units
        )
        if animation:
            self.active_animations.append(animation)
            print(f"  [Animation] Successfully triggered {skill_name} animation" + (" (CRITICAL!)" if is_crit else ""))
        else:
            print(f"  [Animation] WARNING: Animation factory returned None for {skill_name}")

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

    def draw(self):
        """Render the current frame."""
        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake_intensity > 0:
            shake_offset_x = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_offset_y = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)

        # Create main surface
        main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        main_surface.fill(COLOR_BG)

        # Draw grid
        self.draw_grid(main_surface)

        # Draw movement/target range indicators
        self.draw_range_indicators(main_surface)

        # Draw selection highlight (before units so it's behind them)
        if self.selected_unit:
            self.draw_selection_highlight(main_surface, self.selected_unit)

        # Draw units
        for unit in self.units:
            unit.draw(main_surface, self.small_font)

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

        # Draw UI
        self.draw_ui(main_surface)

        # Draw unit info panel (top-right corner) - includes status effects
        self.unit_info_panel.draw(main_surface, SCREEN_WIDTH - 320, 10)

        # Draw skill bar
        self.skill_bar.draw(main_surface, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Draw combat log (bottom-left corner)
        self.combat_log.draw(main_surface, 10, SCREEN_HEIGHT - 230)

        # Apply shake offset and blit to screen
        self.screen.fill(COLOR_BG)
        self.screen.blit(main_surface, (int(shake_offset_x), int(shake_offset_y)))

        # Draw flash overlay
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((*self.flash_color, self.flash_alpha))
            self.screen.blit(flash_surface, (0, 0))

        pygame.display.flip()

    def draw_grid(self, surface: pygame.Surface):
        """Draw the game grid."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = COLOR_GRID_DARK if (x + y) % 2 == 0 else COLOR_GRID_LIGHT

                # Highlight hovered tile
                if self.hovered_grid_pos == (x, y):
                    color = tuple(min(255, c + 30) for c in color)

                rect = pygame.Rect(
                    GRID_OFFSET_X + x * TILE_SIZE,
                    GRID_OFFSET_Y + y * TILE_SIZE,
                    TILE_SIZE, TILE_SIZE
                )
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (30, 34, 42), rect, 1)

    def draw_range_indicators(self, surface: pygame.Surface):
        """Draw movement range, attack range, and skill range indicators."""
        indicator_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Draw movement range (green)
        if self.show_movement_range and self.valid_positions:
            for grid_x, grid_y in self.valid_positions:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*COLOR_MOVEMENT, 80), indicator_surf.get_rect())
                pygame.draw.rect(indicator_surf, (*COLOR_MOVEMENT, 150), indicator_surf.get_rect(), 2)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + grid_x * TILE_SIZE, GRID_OFFSET_Y + grid_y * TILE_SIZE)
                )

        # Draw attack range (red)
        if self.show_target_range and self.attack_positions:
            for grid_x, grid_y in self.attack_positions:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*COLOR_TARGET, 80), indicator_surf.get_rect())
                pygame.draw.rect(indicator_surf, (*COLOR_TARGET, 150), indicator_surf.get_rect(), 2)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + grid_x * TILE_SIZE, GRID_OFFSET_Y + grid_y * TILE_SIZE)
                )

        # Draw skill range (purple/yellow)
        if self.show_skill_range and self.skill_positions:
            skill_color = (200, 150, 255)  # Purple for skills
            for grid_x, grid_y in self.skill_positions:
                indicator_surf.fill((0, 0, 0, 0))
                pygame.draw.rect(indicator_surf, (*skill_color, 80), indicator_surf.get_rect())
                pygame.draw.rect(indicator_surf, (*skill_color, 150), indicator_surf.get_rect(), 2)
                surface.blit(
                    indicator_surf,
                    (GRID_OFFSET_X + grid_x * TILE_SIZE, GRID_OFFSET_Y + grid_y * TILE_SIZE)
                )

    def draw_ui(self, surface: pygame.Surface):
        """Draw UI elements (skill bar, unit info, etc.)."""
        # Draw game state info (top-left corner)
        game_state = self.game_adapter.get_game_state()

        info_lines = [
            f"Turn: {game_state.get('turn', 0)}",
            f"Phase: {game_state.get('phase', 'idle')}",
        ]

        if self.selected_unit:
            info_lines.append(f"Selected: {self.selected_unit.name}")
            info_lines.append(f"HP: {self.selected_unit.hp}/{self.selected_unit.max_hp}")

        y_offset = 10
        for line in info_lines:
            text = self.font.render(line, True, (255, 255, 255))
            surface.blit(text, (10, y_offset))
            y_offset += 25

        # Draw controls help (bottom-left)
        help_text = [
            "ESC - Quit",
            "SPACE - Pause",
            "T - End Turn",
            "1-4,Q-R - Skills",
            "LClick - Select/Move/Attack",
            "RClick - Cancel",
        ]

        y_offset = SCREEN_HEIGHT - len(help_text) * 20 - 10
        for line in help_text:
            text = self.small_font.render(line, True, (150, 150, 150))
            surface.blit(text, (10, y_offset))
            y_offset += 20

        # TODO: Draw skill bar, AP indicator, turn order, etc.

    def execute_turn(self):
        """Execute the current turn (process all planned actions)."""
        if not self.game_adapter.game:
            print("ERROR: No game instance")
            return

        print(f"\n=== Executing Turn {self.game_adapter.game.turn} ===")

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
        self.valid_positions = []
        self.attack_positions = []
        self.skill_positions = []
        self.skill_bar.update(None, None)

        # Execute turn in game logic (headless - no blocking UI callbacks)
        # Skill animations will be triggered by detecting skill usage in sync_state
        print("[Renderer] Setting executing_turn = True")
        self.game_adapter.executing_turn = True

        # Sync state BEFORE turn execution to catch planned skills
        print("[Renderer] Pre-execution sync...")
        pre_events = self.game_adapter.sync_state()
        for event in pre_events:
            self.handle_animation_event(event)

        # Capture status effects snapshot BEFORE turn execution
        # This allows us to detect status effects that are applied and then cleared during execute_turn
        print("[Renderer] Capturing status effects snapshot...")
        self.game_adapter.snapshot_status_effects()

        self.game_adapter.game.execute_turn(ui=None)

        # Sync state AFTER turn execution
        print("[Renderer] Post-execution sync...")
        post_events = self.game_adapter.sync_state()
        for event in post_events:
            self.handle_animation_event(event)

        self.game_adapter.executing_turn = False
        print("[Renderer] Setting executing_turn = False")

        # Fetch messages from game log
        from boneglaive.utils.message_log import message_log
        self.combat_log.add_messages_from_game_log(message_log, count=20)

        # NOTE: DO NOT sync_units_from_game() here!
        # Dead units must remain in visual_units dict until their death animations play
        # They will be removed in the update loop after animations complete

        print(f"Turn {self.game_adapter.game.turn} - Current player: {self.game_adapter.game.current_player}\n")

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

        # Create semi-transparent highlight
        highlight_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (*COLOR_SELECTION, alpha), highlight_surf.get_rect())

        # Draw border
        border_color = (*COLOR_SELECTION, 255)
        pygame.draw.rect(highlight_surf, border_color, highlight_surf.get_rect(), 3)

        # Position on grid
        tile_x = GRID_OFFSET_X + grid_x * TILE_SIZE
        tile_y = GRID_OFFSET_Y + grid_y * TILE_SIZE
        surface.blit(highlight_surf, (tile_x, tile_y))

    def run(self):
        """Main game loop."""
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0  # Convert to seconds

            self.handle_events()
            self.update(delta_time)
            self.draw()

        pygame.quit()


def main():
    """Entry point for graphical version."""
    # Create game state adapter
    adapter = GameStateAdapter()

    # Initialize game with real game logic
    print("Initializing game...")
    adapter.initialize_game(skip_setup=True)
    print(f"Game created with {len(adapter.game.units)} units")

    # Create renderer
    renderer = GraphicalRenderer(adapter)

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
