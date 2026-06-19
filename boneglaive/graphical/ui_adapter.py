#!/usr/bin/env python3
"""
Graphical UI Adapter
Provides the UI interface that engine.py expects for animations.
Bridges between game engine callbacks and pygame renderer.
"""
import pygame
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .renderer import GraphicalRenderer
    from boneglaive.game.units import Unit


class GraphicalUIAdapter:
    """
    UI adapter for graphical version.
    Provides the interface that engine.py expects.
    """

    def __init__(self, renderer: 'GraphicalRenderer'):
        self.renderer = renderer
        self.spinner_active = False
        self.animation_speed = 1.0  # Multiplier for animation speeds

    def start_spinner(self):
        """Start action execution indicator."""
        self.spinner_active = True
        # Could show "Executing Turn..." overlay

    def stop_spinner(self):
        """Stop action execution indicator."""
        self.spinner_active = False

    def advance_spinner(self):
        """Advance spinner animation (called during long operations)."""
        # Just process events and do a quick render
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.renderer.running = False

    def show_attack_animation(self, attacker: 'Unit', target: 'Unit', damage: int = None):
        """
        Show attack animation.

        Args:
            attacker: Attacking unit
            target: Target unit
            damage: Damage dealt
        """

        # Find animated units
        attacker_animated = self.renderer._find_animated_unit_by_game_unit(attacker)
        target_animated = self.renderer._find_animated_unit_by_game_unit(target)

        if not attacker_animated or not target_animated:
            return

        # Trigger shake on target
        if target_animated:
            target_animated.shake_intensity = 10

        # Show damage number
        from .animations import FloatingText
        from .animations.core import COLOR_DAMAGE
        if damage and damage > 0:
            # Convert grid coords to screen coords for floating text
            screen_x, screen_y = self.renderer.grid_to_screen(target_animated.grid_x, target_animated.grid_y)
            damage_text = FloatingText(
                screen_x,
                screen_y,
                f"-{damage}",
                COLOR_DAMAGE
            )
            self.renderer.floating_texts.append(damage_text)

    def show_skill_animation(self, user: 'Unit', skill_name: str, target_pos: tuple = None):
        """
        Show skill animation.

        Args:
            user: Unit using skill
            skill_name: Name of skill
            target_pos: Target position (y, x) in game coords
        """

        # Find animated units
        user_animated = self.renderer._find_animated_unit_by_game_unit(user)
        if not user_animated:
            return

        # Trigger proper skill animation via AnimationFactory
        from boneglaive.graphical.animations import AnimationFactory

        # Find target unit if targeting a unit
        target_unit = None
        if target_pos:
            # Convert game coords (y, x) to grid coords (x, y)
            target_grid_x = target_pos[1]
            target_grid_y = target_pos[0]
            target_unit = self.renderer._get_unit_at_grid(target_grid_x, target_grid_y)

        # Create and trigger animation
        # NOTE: target_pos must be in (grid_y, grid_x) format to match caster_grid_pos format
        animation = AnimationFactory.create_animation(
            skill_name,
            caster_unit=user_animated,
            target_unit=target_unit,
            target_pos=(target_grid_y, target_grid_x) if target_pos else None
        )

        if animation:
            self.renderer.active_animations.append(animation)

        # Flash user unit
        user_animated.flash_alpha = 200

    def show_movement_animation(self, unit: 'Unit', path: list):
        """
        Show movement animation along path.

        Args:
            unit: Unit moving
            path: List of (y, x) positions in game coords
        """

        # Find animated unit
        unit_animated = self.renderer._find_animated_unit_by_game_unit(unit)

        if not unit_animated or not path:
            return

        # Just set final position - smooth animation handled by update loop
        if path:
            final_pos = path[-1]
            y, x = final_pos
            # Convert game coords (y, x) to grid coords (x, y)
            unit_animated.set_target_position(x, y)

    def show_death_animation(self, unit: 'Unit'):
        """
        Show death animation.

        Args:
            unit: Unit that died
        """

        # Find animated unit
        unit_animated = self.renderer._find_animated_unit_by_game_unit(unit)

        if not unit_animated:
            return

        # Death effect: fade out with particles
        unit_animated.is_dead = True

        from boneglaive.graphical.sound_helper import play_sound
        play_sound("unit_death", category="general")

        # Add death particles
        from .animations import DebrisParticle
        for _ in range(20):
            particle = DebrisParticle(
                unit_animated.grid_x,
                unit_animated.grid_y,
                color=(200, 200, 200)
            )
            self.renderer.debris_particles.append(particle)

        # Flash screen
        self.renderer.flash_color = (255, 0, 0)
        self.renderer.flash_alpha = 100
        self.renderer.flash_duration = 0.2

    def draw_board(self, show_cursor=True, show_selection=True, show_attack_targets=True):
        """
        Redraw the board.
        Called by engine during animations.
        """
        # Don't block - let main render loop handle it
        pass

    def _render_and_wait(self, duration: float):
        """
        Render a frame and wait.

        Args:
            duration: Time to wait in seconds
        """
        # Process pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.renderer.running = False

        # Render one frame
        self.renderer.draw()

        # Update display
        pygame.display.flip()

        # Wait
        time.sleep(duration * self.animation_speed)

    def _find_animated_unit_by_game_unit(self, game_unit: 'Unit'):
        """Helper method to find animated unit."""
        return self.renderer._find_animated_unit_by_game_unit(game_unit)
