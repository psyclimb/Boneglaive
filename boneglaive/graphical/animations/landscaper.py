#!/usr/bin/env python3
"""
Graphical animations for the LANDSCAPER unit type.
All skill animations with particles, screen effects, and phased sequencing.

Color scheme matches the Landscaper sprite: burgundy, bone, quartz crystal, dark metal.
"""

import pygame
import random
import math
from typing import Optional, List, Tuple

from boneglaive.graphical.animations.core import (
    TILE_SIZE, Particle, ParticleEmitter
)

try:
    from boneglaive.graphical.sound_helper import play_sound
except ImportError:
    def play_sound(key):
        pass

# ============================================================================
# LANDSCAPER COLOR PALETTE
# ============================================================================

BURGUNDY = (114, 47, 55)
BURGUNDY_DARK = (74, 31, 39)
BURGUNDY_LIGHT = (150, 65, 75)
BONE_IVORY = (224, 213, 197)
BONE_WARM = (139, 115, 85)
QUARTZ_PALE = (224, 224, 255)
QUARTZ_BRIGHT = (232, 232, 255)
DRAGON_EYE = (255, 107, 53)
SLAG_ORANGE = (255, 140, 66)
SLAG_DARK = (139, 69, 19)
TOPIARY_GRAY = (160, 160, 160)
STONE_GRAY = (128, 128, 128)
DARK_METAL = (74, 74, 79)
METAL_LIGHT = (138, 138, 142)


# ============================================================================
# TRANSLATIVE STROKE — Basic Attack (4 rapid tuning fork strikes)
# ============================================================================

class TranslativeStrokeAnimation:
    """4 rapid melee strikes with tuning forks, burgundy particles on each impact."""

    def __init__(self, attacker_unit, target_unit, particle_emitter, screen_shake_callback, **kwargs):
        self.attacker = attacker_unit
        self.target = target_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.active = True
        self.elapsed = 0.0

        # Screen positions
        self.ax = getattr(attacker_unit, 'screen_x', 0)
        self.ay = getattr(attacker_unit, 'screen_y', 0)
        self.tx = getattr(target_unit, 'screen_x', 0)
        self.ty = getattr(target_unit, 'screen_y', 0)

        # 4 strikes at different angles
        self.strike_count = 4
        self.strike_duration = 0.18
        self.total_duration = self.strike_count * self.strike_duration + 0.28
        self.strike_angles = [
            math.radians(-135),  # top-left
            math.radians(-45),   # top-right
            math.radians(45),    # bottom-right
            math.radians(135),   # bottom-left
        ]
        self.current_strike = -1
        self.strike_flashes = []

    def update(self, delta_time):
        self.elapsed += delta_time

        # Determine which strike we're on
        new_strike = min(int(self.elapsed / self.strike_duration), self.strike_count - 1)

        # Trigger new strike
        if new_strike > self.current_strike and new_strike < self.strike_count:
            self.current_strike = new_strike
            # Particles at target
            self.particle_emitter.emit_burst(self.tx, self.ty, BURGUNDY, count=8)
            # Flash
            self.strike_flashes.append({
                'x': self.tx, 'y': self.ty,
                'radius': 5, 'max_radius': 15,
                'alpha': 220, 'lifetime': 0.12
            })
            if self.screen_shake:
                self.screen_shake(3, 0.06)

        # Final impact
        if self.elapsed >= self.strike_count * self.strike_duration and self.current_strike == self.strike_count - 1:
            self.current_strike = self.strike_count  # prevent re-trigger
            self.particle_emitter.emit_burst(self.tx, self.ty, BURGUNDY, count=16)
            self.particle_emitter.emit_burst(self.tx, self.ty, BONE_IVORY, count=6)
            if self.screen_shake:
                self.screen_shake(5, 0.15)

        # Update flashes
        for flash in self.strike_flashes:
            flash['lifetime'] -= delta_time
            flash['radius'] = min(flash['radius'] + 80 * delta_time, flash['max_radius'])
            flash['alpha'] = max(0, flash['alpha'] - 600 * delta_time)
        self.strike_flashes = [f for f in self.strike_flashes if f['lifetime'] > 0]

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        # Draw fork lines for current strike
        strike_idx = min(int(self.elapsed / self.strike_duration), self.strike_count - 1)
        if strike_idx < self.strike_count:
            strike_phase = (self.elapsed % self.strike_duration) / self.strike_duration
            angle = self.strike_angles[strike_idx]
            offset = 20

            # Fork origin offset from attacker
            fork_x = self.ax + math.cos(angle) * offset
            fork_y = self.ay + math.sin(angle) * offset

            # Line extends toward target during wind-up, retracts during recoil
            if strike_phase < 0.35:
                progress = strike_phase / 0.35
                end_x = fork_x + (self.tx - fork_x) * progress
                end_y = fork_y + (self.ty - fork_y) * progress
            elif strike_phase < 0.55:
                end_x = self.tx
                end_y = self.ty
            else:
                retract = (strike_phase - 0.55) / 0.45
                end_x = self.tx + (fork_x - self.tx) * retract
                end_y = self.ty + (fork_y - self.ty) * retract

            alpha = int(200 * (1 - max(0, strike_phase - 0.55) / 0.45))
            if alpha > 0:
                line_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                pygame.draw.line(line_surf, (*QUARTZ_PALE, alpha),
                                (int(fork_x), int(fork_y)),
                                (int(end_x), int(end_y)), 3)
                surface.blit(line_surf, (0, 0))

        # Draw flashes
        for flash in self.strike_flashes:
            if flash['alpha'] > 10:
                flash_surf = pygame.Surface((int(flash['radius'] * 2 + 4), int(flash['radius'] * 2 + 4)), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*QUARTZ_BRIGHT, int(flash['alpha'])),
                                  (int(flash['radius'] + 2), int(flash['radius'] + 2)),
                                  int(flash['radius']))
                surface.blit(flash_surf, (int(flash['x'] - flash['radius'] - 2),
                                          int(flash['y'] - flash['radius'] - 2)))


# ============================================================================
# HORNSWOGGLE — Terrain grab, drag with slag deposit
# ============================================================================

class HornswoggleAnimation:
    """Multi-phase: sonic wave → grab → drag with slag → deposit.
    Uses hidden_tiles to hide terrain changes until the animation reveals them."""

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback
        self.camera = camera

        # Read stored hornswoggle data from game unit
        game_unit = getattr(caster_unit, 'game_unit', None)
        hornswoggle_data = getattr(game_unit, 'last_hornswoggle_data', None) if game_unit else None

        # Tiles hidden from the renderer until animation reveals them
        self.hidden_tiles = set()

        if not hornswoggle_data or not camera:
            self.active = False
            return

        # Convert grid positions to screen positions
        src = hornswoggle_data['source']
        self.source_screen = camera.grid_to_screen(src[1], src[0], centered=True)

        grab = hornswoggle_data['grab_pos']
        self.grab_screen = camera.grid_to_screen(grab[1], grab[0], centered=True)
        self.grab_grid = (grab[1], grab[0])  # (grid_x, grid_y) for hidden_tiles

        deposit = hornswoggle_data['deposit_pos']
        self.deposit_screen = camera.grid_to_screen(deposit[1], deposit[0], centered=True)
        self.deposit_grid = (deposit[1], deposit[0])

        self.slag_screens = []
        self.slag_grids = []  # Grid coords for hiding/revealing
        for pos in hornswoggle_data['slag_positions']:
            self.slag_screens.append(camera.grid_to_screen(pos[1], pos[0], centered=True))
            self.slag_grids.append((pos[1], pos[0]))

        # Calculate wave path tiles (source to grab)
        from boneglaive.game.skills.landscaper import DIRECTION_VECTORS
        direction = hornswoggle_data['direction']
        dy, dx = DIRECTION_VECTORS[direction]
        self.wave_screens = []
        sy, sx = src
        for dist in range(1, 4):
            wy = sy + dy * dist
            wx = sx + dx * dist
            self.wave_screens.append(camera.grid_to_screen(wx, wy, centered=True))
            if (wy, wx) == grab:
                break

        # Phase timing
        self.phase = "wave"
        self.phase_timers = {
            "wave": 0.5,
            "grab": 0.3,
            "drag": 0.35 * max(1, len(self.slag_screens)),
            "deposit": 0.3,
        }

        # Slag formation tracking
        self.slag_formed = [False] * len(self.slag_screens)
        self.terrain_pos = list(self.grab_screen)  # Current flying terrain position
        self.wave_progress = 0.0

        # Initially hide ALL slag walls and the deposit terrain —
        # they already exist in the game map but we reveal them progressively
        for gx, gy in self.slag_grids:
            self.hidden_tiles.add((gx, gy))
        self.hidden_tiles.add(self.deposit_grid)

    def _get_phase_elapsed(self):
        """Get elapsed time within current phase."""
        t = self.elapsed
        for phase_name in ["wave", "grab", "drag", "deposit"]:
            dur = self.phase_timers[phase_name]
            if t <= dur:
                return phase_name, t
            t -= dur
        return "done", 0

    def update(self, delta_time):
        self.elapsed += delta_time
        phase, phase_t = self._get_phase_elapsed()

        if phase == "wave":
            self.wave_progress = phase_t / self.phase_timers["wave"]
            # Emit trail particles along wave front
            if self.wave_screens and self.particle_emitter:
                idx = min(int(self.wave_progress * len(self.wave_screens)), len(self.wave_screens) - 1)
                wx, wy = self.wave_screens[idx]
                self.particle_emitter.emit_trail(wx, wy, QUARTZ_PALE, count=3)

        elif phase == "grab":
            # Grab impact at start of phase
            if phase_t < delta_time * 2 and self.particle_emitter:
                gx, gy = self.grab_screen
                self.particle_emitter.emit_burst(gx, gy, STONE_GRAY, count=20)
                self.particle_emitter.emit_burst(gx, gy, BONE_IVORY, count=8)
                if self.screen_shake:
                    self.screen_shake(6, 0.2)

        elif phase == "drag":
            # Move terrain along drag path, form slag
            drag_dur = self.phase_timers["drag"]
            progress = min(1.0, phase_t / drag_dur) if drag_dur > 0 else 1.0

            # Form slag walls progressively — reveal each one as it forms
            for i in range(len(self.slag_screens)):
                slag_progress = (i + 1) / max(1, len(self.slag_screens) + 1)
                if progress >= slag_progress and not self.slag_formed[i]:
                    self.slag_formed[i] = True
                    sx, sy = self.slag_screens[i]
                    # Reveal this slag tile on the map
                    self.hidden_tiles.discard(self.slag_grids[i])
                    if self.particle_emitter:
                        self.particle_emitter.emit_burst(sx, sy, DRAGON_EYE, count=10)
                        self.particle_emitter.emit_burst(sx, sy, SLAG_ORANGE, count=6)
                    if self.screen_shake:
                        self.screen_shake(4, 0.1)

            # Update flying terrain position (lerp from grab to deposit)
            gx, gy = self.grab_screen
            ddx, ddy = self.deposit_screen
            self.terrain_pos[0] = gx + (ddx - gx) * progress
            self.terrain_pos[1] = gy + (ddy - gy) * progress

            # Trail behind flying terrain
            if self.particle_emitter:
                self.particle_emitter.emit_trail(self.terrain_pos[0], self.terrain_pos[1], BURGUNDY_DARK, count=2)

        elif phase == "deposit":
            # Deposit impact at start — reveal deposit tile
            if phase_t < delta_time * 2:
                self.hidden_tiles.discard(self.deposit_grid)
                ddx, ddy = self.deposit_screen
                if self.particle_emitter:
                    self.particle_emitter.emit_burst(ddx, ddy, STONE_GRAY, count=15)
                    self.particle_emitter.emit_burst(ddx, ddy, BONE_IVORY, count=10)
                if self.screen_shake:
                    self.screen_shake(7, 0.2)
                if self.screen_flash:
                    self.screen_flash(BURGUNDY_DARK, 0.1)
        else:
            # Animation done — make sure everything is revealed
            self.hidden_tiles.clear()
            self.active = False

        return self.active

    def draw(self, surface):
        if not self.active:
            return

        phase, phase_t = self._get_phase_elapsed()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        if phase == "wave":
            # Draw wave arcs traveling toward grab point
            progress = self.wave_progress
            if self.wave_screens:
                idx = min(int(progress * len(self.wave_screens)), len(self.wave_screens) - 1)
                wx, wy = self.wave_screens[idx]
                # Expanding arc at wave front
                radius = int(TILE_SIZE * 0.4)
                alpha = int(180 * (1 - progress * 0.3))
                pygame.draw.circle(overlay, (*QUARTZ_PALE, alpha), (int(wx), int(wy)), radius, 2)
                pygame.draw.circle(overlay, (*QUARTZ_BRIGHT, int(alpha * 0.7)), (int(wx), int(wy)), radius - 4, 2)

        elif phase == "grab":
            # Flash at grab point
            gx, gy = self.grab_screen
            flash_progress = phase_t / self.phase_timers["grab"]
            radius = int(10 + 20 * flash_progress)
            alpha = int(220 * (1 - flash_progress))
            if alpha > 0:
                pygame.draw.circle(overlay, (*QUARTZ_BRIGHT, alpha), (int(gx), int(gy)), radius)

        elif phase == "drag":
            # Draw slag formation effects (glow on newly revealed slag tiles)
            for i, (sx, sy) in enumerate(self.slag_screens):
                if self.slag_formed[i]:
                    pygame.draw.circle(overlay, (*SLAG_ORANGE, 60), (int(sx), int(sy)), int(TILE_SIZE * 0.4))

            # Draw flying terrain block
            tx, ty = self.terrain_pos
            half = TILE_SIZE // 2
            pygame.draw.rect(overlay, (*STONE_GRAY, 200),
                           (int(tx - half * 0.4), int(ty - half * 0.4),
                            int(TILE_SIZE * 0.4), int(TILE_SIZE * 0.4)))
            pygame.draw.rect(overlay, (*BURGUNDY, 80),
                           (int(tx - half * 0.5), int(ty - half * 0.5),
                            int(TILE_SIZE * 0.5), int(TILE_SIZE * 0.5)), 2)

        elif phase == "deposit":
            # Landing flash
            ddx, ddy = self.deposit_screen
            flash_progress = phase_t / self.phase_timers["deposit"]
            radius = int(15 + 10 * flash_progress)
            alpha = int(180 * (1 - flash_progress))
            if alpha > 0:
                pygame.draw.circle(overlay, (*BONE_IVORY, alpha), (int(ddx), int(ddy)), radius)

        surface.blit(overlay, (0, 0))


# ============================================================================
# TOPIARY BREATH — Cone blast, units petrified into stone sculptures
# ============================================================================

class TopiaryBreathAnimation:
    """Cone blast petrifying units into topiary sculptures.
    Uses hidden_tiles to hide topiary terrain until petrification reveals them."""

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback
        self.camera = camera

        # Tiles hidden from the renderer until animation reveals them
        self.hidden_tiles = set()

        # Get cone data from stored execution results
        game_unit = getattr(caster_unit, 'game_unit', None)
        topiary_data = getattr(game_unit, 'last_topiary_breath_data', None) if game_unit else None

        self.cone_screens = []
        self.cone_rows = [[], [], [], []]  # 4 rows of cone tiles
        self.petrify_targets = []  # Screen positions of units being petrified
        self.petrify_grids = []  # Grid coords for hiding/revealing
        self.petrify_started = []

        if camera and topiary_data:
            fire_src = topiary_data['source']
            cone_tiles = topiary_data['cone_tiles']
            transformed_positions = topiary_data.get('transformed_units', [])

            for ty, tx in cone_tiles:
                screen_pos = camera.grid_to_screen(tx, ty, centered=True)
                self.cone_screens.append(screen_pos)

                # Sort into rows by distance
                dist = max(abs(ty - fire_src[0]), abs(tx - fire_src[1]))
                if 1 <= dist <= 4:
                    self.cone_rows[dist - 1].append(screen_pos)

            # Petrification targets from transformed unit positions
            for ty, tx in transformed_positions:
                sx, sy = camera.grid_to_screen(tx, ty, centered=True)
                self.petrify_targets.append((sx, sy))
                self.petrify_grids.append((tx, ty))
                self.petrify_started.append(False)
                # Hide topiary terrain until petrification reveals it
                self.hidden_tiles.add((tx, ty))

        if not self.cone_screens:
            self.active = False
            return

        # Caster screen position (from stored source)
        if topiary_data:
            src = topiary_data['source']
            self.caster_screen = camera.grid_to_screen(src[1], src[0], centered=True)
        elif game_unit:
            self.caster_screen = camera.grid_to_screen(game_unit.x, game_unit.y, centered=True)
        else:
            self.caster_screen = (0, 0)

        self.total_duration = 2.3
        self.cone_alpha = 0
        self.rows_revealed = 0

    def update(self, delta_time):
        self.elapsed += delta_time

        # Phase 1: Charge (0.0-0.4s)
        if self.elapsed < 0.4:
            if self.elapsed < delta_time * 2 and self.screen_shake:
                self.screen_shake(2, 0.3)

        # Phase 2: Cone blast (0.4-1.0s)
        elif self.elapsed < 1.0:
            blast_t = self.elapsed - 0.4
            new_rows = min(4, int(blast_t / 0.15) + 1)
            if new_rows > self.rows_revealed:
                self.rows_revealed = new_rows
                if self.particle_emitter:
                    for sx, sy in self.cone_rows[min(new_rows - 1, 3)]:
                        self.particle_emitter.emit_burst(sx, sy, BURGUNDY, count=4)

            if blast_t < delta_time * 2:
                if self.screen_flash:
                    self.screen_flash(BURGUNDY_DARK, 0.15)

            self.cone_alpha = min(80, int(blast_t * 200))

        # Phase 3: Petrification (1.0-1.8s) — reveal topiary tiles progressively
        elif self.elapsed < 1.8:
            pet_t = self.elapsed - 1.0
            for i, (px, py) in enumerate(self.petrify_targets):
                trigger_time = i * 0.1
                if pet_t >= trigger_time and not self.petrify_started[i]:
                    self.petrify_started[i] = True
                    # Reveal the topiary terrain tile
                    self.hidden_tiles.discard(self.petrify_grids[i])
                    if self.particle_emitter:
                        self.particle_emitter.emit_burst(px, py, TOPIARY_GRAY, count=12)
                        self.particle_emitter.emit_burst(px, py, BURGUNDY, count=8)
                    if self.screen_shake:
                        self.screen_shake(3, 0.08)

        # Phase 4: Settlement (1.8-2.3s)
        elif self.elapsed < 2.3:
            settle_t = self.elapsed - 1.8
            self.cone_alpha = max(0, int(80 * (1 - settle_t / 0.5)))
        else:
            self.hidden_tiles.clear()
            self.active = False

        return self.active

    def draw(self, surface):
        if not self.active:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Draw charge rings (Phase 1)
        if self.elapsed < 0.4:
            charge_t = self.elapsed / 0.4
            cx, cy = self.caster_screen
            for i in range(3):
                radius = int(30 * (1 - charge_t) + 10 * i)
                alpha = int(80 + 80 * charge_t)
                pygame.draw.circle(overlay, (*BURGUNDY, alpha), (int(cx), int(cy)), radius, 2)

        # Draw cone overlay (Phase 2-4)
        if self.cone_alpha > 0 and self.rows_revealed > 0:
            half = TILE_SIZE // 2
            for row_idx in range(self.rows_revealed):
                if row_idx < len(self.cone_rows):
                    for sx, sy in self.cone_rows[row_idx]:
                        pygame.draw.rect(overlay, (*BURGUNDY, self.cone_alpha),
                                       (int(sx - half), int(sy - half), TILE_SIZE, TILE_SIZE))

        # Draw petrification effects (Phase 3)
        if 1.0 <= self.elapsed < 1.8:
            pet_t = self.elapsed - 1.0
            half = TILE_SIZE // 2
            for i, (px, py) in enumerate(self.petrify_targets):
                trigger_time = i * 0.1
                if pet_t >= trigger_time:
                    progress = min(1.0, (pet_t - trigger_time) / 0.4)
                    stone_height = int(TILE_SIZE * progress)
                    pygame.draw.rect(overlay, (*TOPIARY_GRAY, 200),
                                   (int(px - half * 0.6), int(py + half - stone_height),
                                    int(TILE_SIZE * 0.6), stone_height))
                    if progress > 0.6:
                        leaf_alpha = int(200 * min(1, (progress - 0.6) / 0.4))
                        pygame.draw.circle(overlay, (*BURGUNDY, leaf_alpha),
                                         (int(px), int(py - half * 0.3)),
                                         int(TILE_SIZE * 0.3))

        surface.blit(overlay, (0, 0))


# ============================================================================
# LITHOPHONE — Terrain shatter with 8-directional shrapnel
# ============================================================================

class LithophoneAnimation:
    """Acoustic gyre projectile launched from horn array into terrain, shattering it
    from within and sending shrapnel flying in all 8 directions."""

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback
        self.camera = camera

        # Target position (terrain being shattered)
        self.target_x = kwargs.get('target_x', 0)
        self.target_y = kwargs.get('target_y', 0)

        # Caster position
        game_unit = getattr(caster_unit, 'game_unit', None)
        if game_unit and camera:
            self.caster_x, self.caster_y = camera.grid_to_screen(game_unit.x, game_unit.y, centered=True)
        else:
            self.caster_x = kwargs.get('target_x', 0)
            self.caster_y = kwargs.get('target_y', 0)

        # Check if target was a topiary (more dramatic effects)
        self.is_topiary = False
        if game_unit:
            litho_data = getattr(game_unit, 'last_lithophone_data', None)
            if litho_data:
                self.is_topiary = litho_data.get('was_topiary', False)

        # Target grid position for fake terrain drawing
        # The engine already shattered the terrain, so we draw a placeholder
        # during the flight phase to make it look like it's still there
        self.target_grid = None
        if target_pos:
            self.target_grid = (target_pos[1], target_pos[0])  # (grid_x, grid_y)
        self.terrain_visible = True  # False after shatter

        # Gyre projectile state
        self.gyre_x = float(self.caster_x)
        self.gyre_y = float(self.caster_y)
        self.gyre_rotation = 0.0  # Current rotation in radians
        self.gyre_trail = []  # Trail positions for afterimage

        # Shrapnel projectiles (created at shatter)
        self.shrapnel = []
        self.shatter_triggered = False
        self.impact_triggered = False

        # Crack lines for internal shatter effect
        self.cracks = []

        # Phase timing — no charge, projectile fires immediately
        self.flight_end = 0.9
        self.impact_end = 1.15
        self.shatter_end = 1.45
        self.shrapnel_end = 2.1
        self.total_duration = 2.2

    def update(self, delta_time):
        self.elapsed += delta_time

        # Phase 1: Flight — gyre projectile flies straight to target (0.0-0.9s)
        if self.elapsed < self.flight_end:
            flight_t = min(1.0, self.elapsed / self.flight_end)

            # Straight-line interpolation from caster to target
            self.gyre_x = self.caster_x + (self.target_x - self.caster_x) * flight_t
            self.gyre_y = self.caster_y + (self.target_y - self.caster_y) * flight_t

            # Spin the gyre (accelerates during flight)
            spin_speed = 5 + 7 * flight_t  # radians/sec
            self.gyre_rotation += spin_speed * delta_time

            # Append trail point
            self.gyre_trail.append({
                'x': self.gyre_x, 'y': self.gyre_y,
                'rot': self.gyre_rotation,
                'age': 0.0,
            })
            # Age and cull trail
            for tp in self.gyre_trail:
                tp['age'] += delta_time
            self.gyre_trail = [tp for tp in self.gyre_trail if tp['age'] < 0.3]

            # Trail particles
            if self.particle_emitter and random.random() < 0.5:
                self.particle_emitter.emit_trail(self.gyre_x, self.gyre_y, BURGUNDY_DARK, count=1)

        # Phase 2: Impact — gyre hits terrain, terrain absorbs energy
        elif self.elapsed < self.impact_end:
            if not self.impact_triggered:
                self.impact_triggered = True
                if self.screen_shake:
                    self.screen_shake(5, 0.2)
                if self.particle_emitter:
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, BURGUNDY, count=15)
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, QUARTZ_PALE, count=8)
                # Generate crack lines radiating from center
                half = TILE_SIZE // 2
                num_cracks = 6 if not self.is_topiary else 8
                for i in range(num_cracks):
                    angle = (math.tau / num_cracks) * i + random.uniform(-0.2, 0.2)
                    length = random.uniform(half * 0.5, half * 0.95)
                    self.cracks.append({
                        'angle': angle, 'length': length,
                        'width': random.randint(1, 3),
                    })

        # Phase 3: Internal shatter — cracks widen, terrain explodes
        elif self.elapsed < self.shatter_end:
            if not self.shatter_triggered:
                self.shatter_triggered = True
                self.terrain_visible = False  # Terrain is now gone
                intensity = 10 if self.is_topiary else 8
                if self.screen_shake:
                    self.screen_shake(intensity, 0.3)
                if self.screen_flash:
                    self.screen_flash(BURGUNDY_DARK, 0.1)
                if self.particle_emitter:
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, STONE_GRAY, count=35)
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, BONE_IVORY, count=15)
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, BURGUNDY, count=12)
                    if self.is_topiary:
                        self.particle_emitter.emit_burst(self.target_x, self.target_y, BURGUNDY_LIGHT, count=20)

                # Create 8-directional shrapnel
                speed = TILE_SIZE * 4.5
                directions = [(-1, 0), (-1, 1), (0, 1), (1, 1),
                              (1, 0), (1, -1), (0, -1), (-1, -1)]
                for sdy, sdx in directions:
                    # Normalize diagonal speed
                    mag = math.hypot(sdx, sdy)
                    self.shrapnel.append({
                        'x': float(self.target_x),
                        'y': float(self.target_y),
                        'vx': (sdx / mag) * speed,
                        'vy': (sdy / mag) * speed,
                        'lifetime': 0.55,
                        'max_lifetime': 0.55,
                        'size': random.uniform(3, 6),
                        'color': random.choice([STONE_GRAY, BONE_IVORY, BURGUNDY_DARK]),
                        'rotation': random.uniform(0, math.tau),
                        'spin': random.uniform(-15, 15),
                    })

        # Phase 4: Shrapnel flies outward
        elif self.elapsed < self.shrapnel_end:
            for shr in self.shrapnel:
                shr['x'] += shr['vx'] * delta_time
                shr['y'] += shr['vy'] * delta_time
                shr['lifetime'] -= delta_time
                shr['rotation'] += shr['spin'] * delta_time
                # Decelerate slightly
                shr['vx'] *= 0.97
                shr['vy'] *= 0.97
                if self.particle_emitter and random.random() < 0.2:
                    self.particle_emitter.emit_trail(shr['x'], shr['y'], STONE_GRAY, count=1)
            self.shrapnel = [s for s in self.shrapnel if s['lifetime'] > 0]

        # Done
        elif self.elapsed >= self.total_duration:
            self.active = False

        return self.active

    def _draw_gyre(self, surface, cx, cy, rotation, radius, alpha):
        """Draw the acoustic gyre — a spinning vortex ring of resonant energy."""
        alpha = max(0, min(255, int(alpha)))
        if alpha <= 0 or radius < 2:
            return

        icx, icy = int(cx), int(cy)
        ir = int(radius)

        # Filled burgundy disc behind everything for contrast
        pygame.draw.circle(surface, (*BURGUNDY_DARK, int(alpha * 0.45)), (icx, icy), ir)

        # Outer ring — full circle outline in burgundy-light
        pygame.draw.circle(surface, (*BURGUNDY_LIGHT, int(alpha * 0.7)), (icx, icy), ir, max(2, ir // 4))

        # Spinning bright arcs on the outer ring (the "blades" of the vortex)
        outer_w = max(3, ir // 3)
        num_arcs = 4
        arc_span = math.radians(60)
        for i in range(num_arcs):
            arc_angle = rotation + (math.tau / num_arcs) * i
            a1 = arc_angle - arc_span / 2
            a2 = arc_angle + arc_span / 2
            points = []
            for step in range(10):
                t = a1 + (a2 - a1) * step / 9
                px = cx + math.cos(t) * radius
                py = cy + math.sin(t) * radius
                points.append((int(px), int(py)))
            if len(points) >= 2:
                pygame.draw.lines(surface, (*QUARTZ_PALE, alpha), False, points, outer_w)

        # Inner counter-rotating arcs — bright quartz
        inner_r = radius * 0.5
        inner_w = max(2, ir // 4)
        spiral_arcs = 3
        for i in range(spiral_arcs):
            arc_angle = -rotation * 1.5 + (math.tau / spiral_arcs) * i
            a1 = arc_angle - math.radians(45)
            a2 = arc_angle + math.radians(45)
            points = []
            for step in range(8):
                t = a1 + (a2 - a1) * step / 7
                px = cx + math.cos(t) * inner_r
                py = cy + math.sin(t) * inner_r
                points.append((int(px), int(py)))
            if len(points) >= 2:
                pygame.draw.lines(surface, (*QUARTZ_BRIGHT, int(alpha * 0.9)), False, points, inner_w)

        # Bright center core
        core_r = max(3, int(radius * 0.3))
        pygame.draw.circle(surface, (*QUARTZ_PALE, min(255, int(alpha * 1.1))), (icx, icy), core_r)
        pygame.draw.circle(surface, (*BONE_IVORY, alpha), (icx, icy), max(1, core_r - 2))

    def draw(self, surface):
        if not self.active:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Draw fake terrain block at target until shatter
        # (the engine already removed it, but we want it to look intact)
        if self.terrain_visible:
            tx, ty = int(self.target_x), int(self.target_y)
            half = TILE_SIZE // 2
            color = TOPIARY_GRAY if self.is_topiary else STONE_GRAY
            pygame.draw.rect(overlay, (*color, 200),
                           (tx - half, ty - half, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(overlay, (*DARK_METAL, 140),
                           (tx - half, ty - half, TILE_SIZE, TILE_SIZE), 2)

        # Phase 1: Flight — gyre projectile with trail
        if self.elapsed < self.flight_end:
            # Draw trail (fading afterimages)
            for tp in self.gyre_trail:
                trail_alpha = int(100 * max(0, 1 - tp['age'] / 0.3))
                if trail_alpha > 5:
                    trail_r = 12
                    self._draw_gyre(overlay, tp['x'], tp['y'], tp['rot'], trail_r, trail_alpha)

            # Draw main gyre projectile — large and prominent
            flight_t = min(1.0, self.elapsed / self.flight_end)
            base_r = 18
            if flight_t > 0.9:
                gyre_r = base_r * (1 - (flight_t - 0.9) * 3)
            else:
                gyre_r = base_r
            gyre_r = max(6, gyre_r)

            # Soft glow behind (drawn first so gyre is on top)
            glow_r = int(gyre_r * 1.8)
            pygame.draw.circle(overlay, (*BURGUNDY_DARK, 30), (int(self.gyre_x), int(self.gyre_y)), glow_r)

            # The gyre itself
            self._draw_gyre(overlay, self.gyre_x, self.gyre_y, self.gyre_rotation, gyre_r, 240)

        # Phase 2: Impact — gyre absorbed, cracks appear on terrain
        elif self.elapsed < self.impact_end:
            impact_t = (self.elapsed - self.flight_end) / (self.impact_end - self.flight_end)
            half = TILE_SIZE // 2
            tx, ty = int(self.target_x), int(self.target_y)

            # Imploding gyre flash (shrinks into terrain)
            implode_r = int(12 * (1 - impact_t))
            if implode_r > 0:
                self._draw_gyre(overlay, tx, ty, self.gyre_rotation + self.elapsed * 20, implode_r, int(200 * (1 - impact_t)))

            # Burgundy glow pulsing on terrain tile
            glow_alpha = max(0, min(255, int(80 + 100 * math.sin(impact_t * math.pi * 3))))
            if glow_alpha > 0:
                pygame.draw.rect(overlay, (*BURGUNDY, glow_alpha),
                               (tx - half, ty - half, TILE_SIZE, TILE_SIZE))

            # Crack lines spreading from center
            crack_progress = min(1.0, impact_t * 2)  # Cracks spread fast
            for crack in self.cracks:
                cl = crack['length'] * crack_progress
                ex = tx + math.cos(crack['angle']) * cl
                ey = ty + math.sin(crack['angle']) * cl
                alpha = int(200 * min(1, impact_t * 3))
                pygame.draw.line(overlay, (*QUARTZ_BRIGHT, alpha),
                               (tx, ty), (int(ex), int(ey)), crack['width'])

        # Phase 4: Shatter explosion
        elif self.elapsed < self.shatter_end:
            shatter_t = (self.elapsed - self.impact_end) / (self.shatter_end - self.impact_end)
            tx, ty = int(self.target_x), int(self.target_y)

            # Expanding shatter burst — burgundy core with dragon_eye ring
            burst_r = int(8 + 35 * shatter_t)
            burst_alpha = int(240 * (1 - shatter_t))
            if burst_alpha > 0:
                pygame.draw.circle(overlay, (*BURGUNDY, burst_alpha), (tx, ty), burst_r)
                ring_r = int(burst_r * 1.3)
                ring_alpha = int(180 * (1 - shatter_t))
                if ring_alpha > 0:
                    pygame.draw.circle(overlay, (*DRAGON_EYE, ring_alpha), (tx, ty), ring_r, 3)

            # Crack lines flash bright then fade
            for crack in self.cracks:
                cl = crack['length'] * (1 + shatter_t * 0.5)
                ex = tx + math.cos(crack['angle']) * cl
                ey = ty + math.sin(crack['angle']) * cl
                alpha = int(255 * max(0, 1 - shatter_t * 2))
                if alpha > 0:
                    pygame.draw.line(overlay, (*QUARTZ_BRIGHT, alpha),
                                   (tx, ty), (int(ex), int(ey)), crack['width'] + 1)

        # Phase 5: Shrapnel pieces flying
        for shr in self.shrapnel:
            if shr['lifetime'] > 0:
                fade = shr['lifetime'] / shr['max_lifetime']
                alpha = int(240 * fade)
                size = max(1, int(shr['size'] * (0.5 + 0.5 * fade)))
                sx, sy = int(shr['x']), int(shr['y'])
                # Draw as small angular fragments (rotated squares)
                rot = shr['rotation']
                hs = size
                pts = []
                for corner in range(4):
                    a = rot + corner * math.pi / 2
                    pts.append((sx + int(math.cos(a) * hs), sy + int(math.sin(a) * hs)))
                pygame.draw.polygon(overlay, (*shr['color'], alpha), pts)

        surface.blit(overlay, (0, 0))


# ============================================================================
# SLAG WALL DESPAWN — Crumble animation when slag expires
# ============================================================================

class SlagWallDespawnAnimation:
    """Slag wall crumbles to dust."""

    def __init__(self, caster_unit=None, target_unit=None, target_pos=None,
                 particle_emitter=None, screen_shake_callback=None,
                 screen_flash_callback=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.total_duration = 0.6

        self.target_x = kwargs.get('target_x', 0)
        self.target_y = kwargs.get('target_y', 0)

        self.crumbled = False

    def update(self, delta_time):
        self.elapsed += delta_time

        if not self.crumbled and self.elapsed > 0.1:
            self.crumbled = True
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.target_x, self.target_y, SLAG_DARK, count=15)
                self.particle_emitter.emit_burst(self.target_x, self.target_y, DRAGON_EYE, count=5)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active or self.elapsed >= self.total_duration:
            return
        # Fading crack overlay
        if self.crumbled:
            progress = min(1.0, (self.elapsed - 0.1) / 0.5)
            alpha = int(120 * (1 - progress))
            if alpha > 0:
                overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                # Crack lines
                pygame.draw.line(overlay, (*SLAG_DARK, alpha), (8, 8), (56, 56), 2)
                pygame.draw.line(overlay, (*SLAG_DARK, alpha), (56, 8), (8, 56), 2)
                half = TILE_SIZE // 2
                surface.blit(overlay, (int(self.target_x - half), int(self.target_y - half)))


# ============================================================================
# TOPIARY REVERT — Stone shell shatters, unit emerges
# ============================================================================

class TopiaryRevertAnimation:
    """Topiary sculpture cracks and shatters, revealing the unit inside."""

    def __init__(self, caster_unit=None, target_unit=None, target_pos=None,
                 particle_emitter=None, screen_shake_callback=None,
                 screen_flash_callback=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.total_duration = 0.8

        self.target_x = kwargs.get('target_x', 0)
        self.target_y = kwargs.get('target_y', 0)

        self.shattered = False

    def update(self, delta_time):
        self.elapsed += delta_time

        # Phase 1: Cracks (0.0-0.4s)
        if self.elapsed < 0.4:
            pass  # Visual only in draw

        # Phase 2: Shatter (0.4-0.8s)
        elif not self.shattered:
            self.shattered = True
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.target_x, self.target_y, STONE_GRAY, count=20)
                self.particle_emitter.emit_burst(self.target_x, self.target_y, BURGUNDY, count=15)
                self.particle_emitter.emit_burst(self.target_x, self.target_y, QUARTZ_PALE, count=5)
            if self.screen_shake:
                self.screen_shake(4, 0.15)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        half = TILE_SIZE // 2

        if self.elapsed < 0.4:
            # Cracks spreading on topiary
            progress = self.elapsed / 0.4
            crack_len = int(half * progress)
            alpha = int(200 * progress)
            cx, cy = int(self.target_x), int(self.target_y)
            pygame.draw.line(overlay, (*STONE_GRAY, alpha),
                           (cx - crack_len, cy - crack_len), (cx + crack_len, cy + crack_len), 2)
            pygame.draw.line(overlay, (*STONE_GRAY, alpha),
                           (cx + crack_len, cy - crack_len), (cx - crack_len, cy + crack_len), 2)
            pygame.draw.line(overlay, (*BONE_IVORY, int(alpha * 0.6)),
                           (cx, cy - crack_len), (cx, cy + crack_len), 2)
        elif self.elapsed < 0.8:
            # Emergence flash
            progress = (self.elapsed - 0.4) / 0.4
            radius = int(10 + 15 * progress)
            alpha = int(180 * (1 - progress))
            if alpha > 0:
                pygame.draw.circle(overlay, (*QUARTZ_PALE, alpha),
                                  (int(self.target_x), int(self.target_y)), radius)

        surface.blit(overlay, (0, 0))
