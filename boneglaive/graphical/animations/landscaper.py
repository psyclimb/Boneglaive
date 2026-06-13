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

from boneglaive.graphical.sound_helper import play_sound

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
# TRANSLATIVE STROKE — Basic Attack (4 simultaneous tuning fork strikes)
# ============================================================================

class TranslativeStrokeAnimation:
    """All 4 tuning forks strike the target simultaneously, then a quartz watch
    mechanism effect plays on the Landscaper representing cooldown cycling."""

    def __init__(self, attacker_unit, target_unit, particle_emitter, screen_shake_callback, **kwargs):
        self.attacker = attacker_unit
        self.target = target_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.active = True
        self.elapsed = 0.0

        # Screen-absolute positions
        self.ax = attacker_unit.x
        self.ay = attacker_unit.y
        self.tx = target_unit.x
        self.ty = target_unit.y

        # Direction from attacker to target
        dx = self.tx - self.ax
        dy = self.ty - self.ay
        dist = math.hypot(dx, dy) or 1.0
        self.dir_x = dx / dist
        self.dir_y = dy / dist
        self.dist = dist
        self.perp_x = -self.dir_y
        self.perp_y = self.dir_x

        # 4 fork origins — fanned out from attacker position
        spread = 14
        self.fork_origins = [
            (self.ax + self.perp_x * spread * 1.2 - self.dir_x * 8,
             self.ay + self.perp_y * spread * 1.2 - self.dir_y * 8),
            (self.ax + self.perp_x * spread * 0.4 + self.dir_x * 4,
             self.ay + self.perp_y * spread * 0.4 + self.dir_y * 4),
            (self.ax - self.perp_x * spread * 0.4 + self.dir_x * 4,
             self.ay - self.perp_y * spread * 0.4 + self.dir_y * 4),
            (self.ax - self.perp_x * spread * 1.2 - self.dir_x * 8,
             self.ay - self.perp_y * spread * 1.2 - self.dir_y * 8),
        ]

        # Phase timing
        self.strike_end = 0.35    # All forks thrust simultaneously
        self.impact_end = 0.5     # Impact hold / flash
        self.watch_end = 1.2      # Quartz watch effect on Landscaper
        self.total_duration = self.watch_end

        # State
        self.impact_triggered = False
        self.swing_sound_played = False
        self.watch_hand_angle = 0.0  # Current hand rotation

    def update(self, delta_time):
        self.elapsed += delta_time

        # Phase 1: Fork swing sound
        if not self.swing_sound_played:
            self.swing_sound_played = True
            play_sound("translative_stroke_swing")

        # Phase 2: Impact trigger
        if self.elapsed >= self.strike_end and not self.impact_triggered:
            self.impact_triggered = True
            play_sound("translative_stroke_impact")
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, BURGUNDY, count=18)
                self.particle_emitter.emit_burst(self.tx, self.ty, QUARTZ_PALE, count=8)
            if self.screen_shake:
                self.screen_shake(6, 0.12)
            # Shake the target unit
            if self.target:
                self.target.shake_intensity = 12

        # Phase 3: Quartz watch — spin the hand (accelerating)
        if self.elapsed >= self.impact_end:
            watch_t = (self.elapsed - self.impact_end) / (self.watch_end - self.impact_end)
            # Accelerating clockwise spin: starts slow, speeds up
            speed = 4 + 12 * watch_t  # radians/sec, accelerates
            self.watch_hand_angle += speed * delta_time

            # Particles drifting inward toward Landscaper
            if self.particle_emitter and random.random() < 0.4:
                angle = random.uniform(0, math.tau)
                dist = random.uniform(20, 35)
                px = self.ax + math.cos(angle) * dist
                py = self.ay + math.sin(angle) * dist
                self.particle_emitter.emit_trail(px, py, BURGUNDY_LIGHT, count=1)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # === Phase 1: Fork thrust (0.0 – strike_end) ===
        if self.elapsed < self.impact_end:
            thrust_t = min(1.0, self.elapsed / self.strike_end)

            for ox, oy in self.fork_origins:
                # Fork tip position — lerp from origin toward target
                if thrust_t < 1.0:
                    tip_x = ox + (self.tx - ox) * thrust_t
                    tip_y = oy + (self.ty - oy) * thrust_t
                else:
                    tip_x, tip_y = self.tx, self.ty

                # Direction from this fork's origin to target
                fdx = self.tx - ox
                fdy = self.ty - oy
                fmag = math.hypot(fdx, fdy) or 1
                fdx /= fmag
                fdy /= fmag
                fperp_x = -fdy
                fperp_y = fdx

                # Alpha: full during thrust, fade during impact hold
                if self.elapsed < self.strike_end:
                    fork_alpha = 230
                else:
                    fade = (self.elapsed - self.strike_end) / (self.impact_end - self.strike_end)
                    fork_alpha = max(0, int(230 * (1 - fade)))

                if fork_alpha > 5:
                    # Handle (bone ivory line from origin toward tip)
                    handle_end_x = tip_x - fdx * 8
                    handle_end_y = tip_y - fdy * 8
                    pygame.draw.line(overlay, (*BONE_IVORY, fork_alpha),
                                   (int(ox), int(oy)), (int(handle_end_x), int(handle_end_y)), 3)

                    # Two tines from handle end, spreading toward tip
                    tine_spread = 4
                    t1x = tip_x + fperp_x * tine_spread
                    t1y = tip_y + fperp_y * tine_spread
                    t2x = tip_x - fperp_x * tine_spread
                    t2y = tip_y - fperp_y * tine_spread
                    pygame.draw.line(overlay, (*QUARTZ_PALE, fork_alpha),
                                   (int(handle_end_x), int(handle_end_y)), (int(t1x), int(t1y)), 2)
                    pygame.draw.line(overlay, (*QUARTZ_PALE, fork_alpha),
                                   (int(handle_end_x), int(handle_end_y)), (int(t2x), int(t2y)), 2)

                    # Crystal glow at the tip
                    pygame.draw.circle(overlay, (*QUARTZ_BRIGHT, int(fork_alpha * 0.5)),
                                     (int(tip_x), int(tip_y)), 3)

        # === Impact flash at target ===
        if self.strike_end <= self.elapsed < self.impact_end:
            flash_t = (self.elapsed - self.strike_end) / (self.impact_end - self.strike_end)
            flash_r = int(6 + 12 * flash_t)
            flash_a = max(0, min(255, int(200 * (1 - flash_t))))
            if flash_a > 0:
                pygame.draw.circle(overlay, (*BURGUNDY, flash_a),
                                 (int(self.tx), int(self.ty)), flash_r)
                pygame.draw.circle(overlay, (*QUARTZ_PALE, int(flash_a * 0.6)),
                                 (int(self.tx), int(self.ty)), max(1, flash_r // 2))

        # === Phase 3: Quartz watch mechanism on the Landscaper ===
        if self.elapsed >= self.impact_end:
            watch_t = min(1.0, (self.elapsed - self.impact_end) / (self.watch_end - self.impact_end))
            # Fade in then out
            if watch_t < 0.15:
                watch_alpha = int(220 * (watch_t / 0.15))
            elif watch_t > 0.7:
                watch_alpha = max(0, int(220 * (1 - (watch_t - 0.7) / 0.3)))
            else:
                watch_alpha = 220

            cx, cy = int(self.ax), int(self.ay)
            watch_r = 18

            # Outer bezel — burgundy circle
            pygame.draw.circle(overlay, (*BURGUNDY, watch_alpha), (cx, cy), watch_r, 2)
            pygame.draw.circle(overlay, (*BURGUNDY_DARK, int(watch_alpha * 0.3)), (cx, cy), watch_r)

            # Tick marks around the dial (12 marks like a clock)
            num_ticks = 12
            for i in range(num_ticks):
                tick_angle = (math.tau / num_ticks) * i
                inner_r = watch_r - 4
                outer_r = watch_r - 1
                ix = cx + math.cos(tick_angle) * inner_r
                iy = cy + math.sin(tick_angle) * inner_r
                ox_t = cx + math.cos(tick_angle) * outer_r
                oy_t = cy + math.sin(tick_angle) * outer_r
                tick_a = max(0, min(255, int(watch_alpha * 0.7)))
                pygame.draw.line(overlay, (*BONE_IVORY, tick_a),
                               (int(ix), int(iy)), (int(ox_t), int(oy_t)), 1)

            # Sweeping hand — quartz bright, rotates clockwise (accelerating)
            hand_len = watch_r - 5
            # Negative angle for clockwise (pygame y-axis is down)
            hx = cx + math.cos(self.watch_hand_angle) * hand_len
            hy = cy + math.sin(self.watch_hand_angle) * hand_len
            hand_a = max(0, min(255, watch_alpha))
            pygame.draw.line(overlay, (*QUARTZ_BRIGHT, hand_a),
                           (cx, cy), (int(hx), int(hy)), 2)
            # Bright tip
            pygame.draw.circle(overlay, (*QUARTZ_PALE, hand_a), (int(hx), int(hy)), 2)

            # Center crystal — pulsing
            pulse = 0.5 + 0.5 * math.sin(self.elapsed * 12)
            crystal_a = max(0, min(255, int(watch_alpha * (0.6 + 0.4 * pulse))))
            pygame.draw.circle(overlay, (*QUARTZ_PALE, crystal_a), (cx, cy), 4)
            pygame.draw.circle(overlay, (*BURGUNDY_LIGHT, int(crystal_a * 0.5)), (cx, cy), 2)

        surface.blit(overlay, (0, 0))


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
        self.is_whiff = hornswoggle_data.get('whiff', False)

        from boneglaive.game.skills.landscaper import DIRECTION_VECTORS, HornswoggleSkill
        direction = hornswoggle_data['direction']
        dy, dx = DIRECTION_VECTORS[direction]

        if self.is_whiff:
            # Whiff mode: wave travels full range and dissipates
            self.wave_screens = []
            sy, sx = src
            for dist in range(1, HornswoggleSkill.WAVE_RANGE + 1):
                wy = sy + dy * dist
                wx = sx + dx * dist
                if not (0 <= wy < 10 and 0 <= wx < 20):  # Map bounds
                    break
                self.wave_screens.append(camera.grid_to_screen(wx, wy, centered=True))

            # Compute wave angle from source toward last wave tile
            sx_screen, sy_screen = self.source_screen
            if self.wave_screens:
                end_x, end_y = self.wave_screens[-1]
            else:
                end_x = sx_screen + dx * 100
                end_y = sy_screen + dy * 100
            self.wave_angle = math.atan2(end_y - sy_screen, end_x - sx_screen)

            # No grab/drag/deposit/sympathetic
            self.grab_screen = self.wave_screens[-1] if self.wave_screens else self.source_screen
            self.grab_grid = (0, 0)
            self.deposit_screen = self.grab_screen
            self.deposit_grid = (0, 0)
            self.slag_screens = []
            self.slag_grids = []
            self.sympathetic_screens = []
            self.sympathetic_grids = []
            self.sympathetic_formed = []

            # Phase timing: wave only
            self.phase = "wave"
            self.phase_order = ["wave"]
            self.phase_timers = {"wave": 0.56}

            self.slag_formed = []
            self.terrain_pos = list(self.grab_screen)
            self.wave_progress = 0.0
            self.wave_sound_played = False
            self.grab_sound_played = False
            self.slag_sound_played = False
            self.deposit_sound_played = False

            self.wave_x = float(sx_screen)
            self.wave_y = float(sy_screen)
            self.wave_rotation = 0.0
            self.wave_trail = []
            return

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
        self.wave_screens = []
        sy, sx = src
        for dist in range(1, HornswoggleSkill.WAVE_RANGE + 1):
            wy = sy + dy * dist
            wx = sx + dx * dist
            self.wave_screens.append(camera.grid_to_screen(wx, wy, centered=True))
            if (wy, wx) == grab:
                break

        # Wave flight angle for drawing directional arcs
        sx_screen, sy_screen = self.source_screen
        gx_screen, gy_screen = self.grab_screen
        self.wave_angle = math.atan2(gy_screen - sy_screen, gx_screen - sx_screen)

        # Sympathetic Resonance upgrade data
        self.sympathetic_screens = []
        self.sympathetic_grids = []  # (from_grid, to_grid) pairs
        self.sympathetic_formed = []
        sym_drags = hornswoggle_data.get('sympathetic_drags', [])
        for sd in sym_drags:
            from_pos = sd['from']
            to_pos = sd['to']
            self.sympathetic_screens.append({
                'from': camera.grid_to_screen(from_pos[1], from_pos[0], centered=True),
                'to': camera.grid_to_screen(to_pos[1], to_pos[0], centered=True),
            })
            self.sympathetic_grids.append({
                'from': (from_pos[1], from_pos[0]),
                'to': (to_pos[1], to_pos[0]),
            })
            self.sympathetic_formed.append(False)

        # Phase timing
        self.phase = "wave"
        self.phase_order = ["wave", "grab", "drag", "deposit"]
        self.phase_timers = {
            "wave": 0.56,
            "grab": 0.24,
            "drag": 0.28 * max(1, len(self.slag_screens)),
            "deposit": 0.24,
        }
        if self.sympathetic_screens:
            self.phase_order.append("sympathetic")
            self.phase_timers["sympathetic"] = 0.12 * max(1, len(self.sympathetic_screens))

        # Slag formation tracking
        self.slag_formed = [False] * len(self.slag_screens)
        self.terrain_pos = list(self.grab_screen)  # Current flying terrain position
        self.wave_progress = 0.0
        self.wave_sound_played = False
        self.grab_sound_played = False
        self.slag_sound_played = False
        self.deposit_sound_played = False

        # Wave projectile state
        self.wave_x = float(sx_screen)
        self.wave_y = float(sy_screen)
        self.wave_rotation = 0.0
        self.wave_trail = []  # Trail of past positions for fading arcs

        # Initially hide ALL slag walls and the deposit terrain —
        # they already exist in the game map but we reveal them progressively
        for gx, gy in self.slag_grids:
            self.hidden_tiles.add((gx, gy))
        self.hidden_tiles.add(self.deposit_grid)
        # Hide sympathetic destinations and slag (source becomes slag, dest becomes terrain)
        for sg in self.sympathetic_grids:
            self.hidden_tiles.add(sg['from'])
            self.hidden_tiles.add(sg['to'])

    def _get_phase_elapsed(self):
        """Get elapsed time within current phase."""
        t = self.elapsed
        for phase_name in self.phase_order:
            dur = self.phase_timers[phase_name]
            if t <= dur:
                return phase_name, t
            t -= dur
        return "done", 0

    def update(self, delta_time):
        if not self.active:
            return False
        self.elapsed += delta_time
        phase, phase_t = self._get_phase_elapsed()

        if phase == "wave":
            if not self.wave_sound_played:
                self.wave_sound_played = True
                play_sound("hornswoggle_wave")
            self.wave_progress = phase_t / self.phase_timers["wave"]
            progress = self.wave_progress

            # Interpolate wave position along straight line from source to grab
            sx, sy = self.source_screen
            gx, gy = self.grab_screen
            self.wave_x = sx + (gx - sx) * progress
            self.wave_y = sy + (gy - sy) * progress

            self.wave_rotation += 6 * delta_time

            # Append trail
            self.wave_trail.append({
                'x': self.wave_x, 'y': self.wave_y,
                'rot': self.wave_rotation, 'age': 0.0,
            })
            for tp in self.wave_trail:
                tp['age'] += delta_time
            self.wave_trail = [tp for tp in self.wave_trail if tp['age'] < 0.35]

            # Particles along wave front
            if self.particle_emitter and random.random() < 0.5:
                self.particle_emitter.emit_trail(self.wave_x, self.wave_y, BURGUNDY_DARK, count=1)

        elif phase == "grab":
            # Grab impact at start of phase
            if not self.grab_sound_played:
                self.grab_sound_played = True
                play_sound("hornswoggle_grab")
            if phase_t < delta_time * 2 and self.particle_emitter:
                gx, gy = self.grab_screen
                self.particle_emitter.emit_burst(gx, gy, BURGUNDY, count=15)
                self.particle_emitter.emit_burst(gx, gy, STONE_GRAY, count=12)
                self.particle_emitter.emit_burst(gx, gy, BONE_IVORY, count=6)
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
                    if not self.slag_sound_played:
                        self.slag_sound_played = True
                        play_sound("hornswoggle_slag")
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
            if not self.deposit_sound_played:
                self.deposit_sound_played = True
                play_sound("hornswoggle_deposit")
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

        elif phase == "sympathetic":
            # Sympathetic Resonance — reveal tiles progressively
            sym_dur = self.phase_timers["sympathetic"]
            progress = min(1.0, phase_t / sym_dur) if sym_dur > 0 else 1.0
            n = len(self.sympathetic_screens)

            for i in range(n):
                threshold = (i + 1) / max(1, n + 1)
                if progress >= threshold and not self.sympathetic_formed[i]:
                    self.sympathetic_formed[i] = True
                    sg = self.sympathetic_grids[i]
                    ss = self.sympathetic_screens[i]
                    # Reveal slag at source and terrain at destination
                    self.hidden_tiles.discard(sg['from'])
                    self.hidden_tiles.discard(sg['to'])
                    # Particles at destination
                    dx, dy = ss['to']
                    if self.particle_emitter:
                        self.particle_emitter.emit_burst(dx, dy, STONE_GRAY, count=8)
                        self.particle_emitter.emit_burst(dx, dy, BURGUNDY, count=4)
                    # Slag glow at source
                    sx, sy = ss['from']
                    if self.particle_emitter:
                        self.particle_emitter.emit_burst(sx, sy, SLAG_ORANGE, count=6)
                    if self.screen_shake:
                        self.screen_shake(3, 0.08)
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
            # Draw trail — fading pressure arcs behind the wave front
            for tp in self.wave_trail:
                trail_alpha = max(0, min(255, int(100 * (1 - tp['age'] / 0.35))))
                if trail_alpha > 5:
                    r = 10
                    # Concentric pressure arcs perpendicular to travel direction
                    perp = self.wave_angle + math.pi / 2
                    for arc_i in range(2):
                        arc_offset = (arc_i - 0.5) * r * 0.6
                        ax = tp['x'] + math.cos(perp) * arc_offset
                        ay = tp['y'] + math.sin(perp) * arc_offset
                        pygame.draw.circle(overlay, (*BURGUNDY, trail_alpha), (int(ax), int(ay)), int(r * 0.5), 1)

            # Draw main wave projectile — acoustic pressure front
            wx, wy = int(self.wave_x), int(self.wave_y)
            wave_r = 14

            # Filled burgundy core
            pygame.draw.circle(overlay, (*BURGUNDY_DARK, 140), (wx, wy), wave_r)

            # Pressure arcs — bright arcs perpendicular to travel
            perp = self.wave_angle + math.pi / 2
            arc_w = max(2, wave_r // 3)
            for arc_i in range(3):
                # Three arcs stacked perpendicular to direction of travel
                offset = (arc_i - 1) * wave_r * 0.55
                ax = wx + math.cos(perp) * offset
                ay = wy + math.sin(perp) * offset
                arc_r = int(wave_r * 0.45)
                pygame.draw.circle(overlay, (*QUARTZ_PALE, 200), (int(ax), int(ay)), arc_r, arc_w)

            # Bright leading edge — a line perpendicular to travel at the front
            front_len = wave_r * 1.2
            fx1 = wx + math.cos(perp) * front_len
            fy1 = wy + math.sin(perp) * front_len
            fx2 = wx - math.cos(perp) * front_len
            fy2 = wy - math.sin(perp) * front_len
            pygame.draw.line(overlay, (*QUARTZ_BRIGHT, 180),
                           (int(fx1), int(fy1)), (int(fx2), int(fy2)), 3)

            # Inner burgundy-light ring
            pygame.draw.circle(overlay, (*BURGUNDY_LIGHT, 160), (wx, wy), int(wave_r * 0.5), 2)

            # Bright core dot
            pygame.draw.circle(overlay, (*QUARTZ_PALE, 220), (wx, wy), 3)

        elif phase == "grab":
            # Burgundy flash at grab point
            gx, gy = self.grab_screen
            flash_progress = phase_t / self.phase_timers["grab"]
            radius = int(12 + 18 * flash_progress)
            alpha = max(0, min(255, int(220 * (1 - flash_progress))))
            if alpha > 0:
                pygame.draw.circle(overlay, (*BURGUNDY, alpha), (int(gx), int(gy)), radius)
                inner_alpha = max(0, min(255, int(180 * (1 - flash_progress))))
                pygame.draw.circle(overlay, (*QUARTZ_PALE, inner_alpha), (int(gx), int(gy)), int(radius * 0.5))

        elif phase == "drag":
            # Draw slag formation effects (glow on newly revealed slag tiles)
            for i, (sx, sy) in enumerate(self.slag_screens):
                if self.slag_formed[i]:
                    pygame.draw.circle(overlay, (*SLAG_ORANGE, 60), (int(sx), int(sy)), int(TILE_SIZE * 0.4))

            # Draw flying terrain block with burgundy resonance glow
            tx, ty = self.terrain_pos
            half = TILE_SIZE // 2
            # Burgundy glow around terrain
            pygame.draw.rect(overlay, (*BURGUNDY_DARK, 60),
                           (int(tx - half * 0.6), int(ty - half * 0.6),
                            int(TILE_SIZE * 0.6), int(TILE_SIZE * 0.6)))
            # Terrain body
            pygame.draw.rect(overlay, (*STONE_GRAY, 210),
                           (int(tx - half * 0.4), int(ty - half * 0.4),
                            int(TILE_SIZE * 0.4), int(TILE_SIZE * 0.4)))
            # Burgundy resonance border
            pygame.draw.rect(overlay, (*BURGUNDY_LIGHT, 160),
                           (int(tx - half * 0.45), int(ty - half * 0.45),
                            int(TILE_SIZE * 0.45), int(TILE_SIZE * 0.45)), 2)

        elif phase == "deposit":
            # Landing flash
            ddx, ddy = self.deposit_screen
            flash_progress = phase_t / self.phase_timers["deposit"]
            radius = int(15 + 10 * flash_progress)
            alpha = int(180 * (1 - flash_progress))
            if alpha > 0:
                pygame.draw.circle(overlay, (*BONE_IVORY, alpha), (int(ddx), int(ddy)), radius)

        elif phase == "sympathetic":
            # Sympathetic Resonance — tiles sliding from source to destination
            sym_dur = self.phase_timers["sympathetic"]
            progress = min(1.0, phase_t / sym_dur) if sym_dur > 0 else 1.0
            n = len(self.sympathetic_screens)
            half = TILE_SIZE // 2

            for i in range(n):
                threshold = (i + 1) / max(1, n + 1)
                ss = self.sympathetic_screens[i]
                fx, fy = ss['from']
                tx, ty = ss['to']

                if self.sympathetic_formed[i]:
                    # Already landed — draw fading glow at destination
                    fade = max(0, 1.0 - (progress - threshold) * 4)
                    if fade > 0:
                        glow_alpha = int(100 * fade)
                        pygame.draw.circle(overlay, (*BURGUNDY, glow_alpha),
                                         (int(tx), int(ty)), int(TILE_SIZE * 0.35))
                        # Slag glow at source
                        slag_alpha = int(80 * fade)
                        pygame.draw.circle(overlay, (*SLAG_ORANGE, slag_alpha),
                                         (int(fx), int(fy)), int(TILE_SIZE * 0.3))
                else:
                    # Sliding — interpolate position from source to dest
                    local_t = progress / threshold if threshold > 0 else 1.0
                    local_t = min(1.0, local_t)
                    # Ease out
                    eased = 1 - (1 - local_t) * (1 - local_t)
                    cx = fx + (tx - fx) * eased
                    cy = fy + (ty - fy) * eased

                    # Burgundy resonance glow
                    pygame.draw.circle(overlay, (*BURGUNDY_DARK, 50),
                                     (int(cx), int(cy)), int(TILE_SIZE * 0.4))
                    # Terrain block
                    block_s = int(TILE_SIZE * 0.35)
                    bhs = block_s // 2
                    pygame.draw.rect(overlay, (*STONE_GRAY, 200),
                                   (int(cx - bhs), int(cy - bhs), block_s, block_s))
                    pygame.draw.rect(overlay, (*BURGUNDY_LIGHT, 150),
                                   (int(cx - bhs), int(cy - bhs), block_s, block_s), 2)

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
            terrain_topiary_positions = topiary_data.get('terrain_topiaries', [])
            generated_topiary_positions = topiary_data.get('generated_topiaries', [])

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

            # Terrain and generated topiaries (upgraded) get same reveal treatment
            for ty, tx in terrain_topiary_positions + generated_topiary_positions:
                sx, sy = camera.grid_to_screen(tx, ty, centered=True)
                self.petrify_targets.append((sx, sy))
                self.petrify_grids.append((tx, ty))
                self.petrify_started.append(False)
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
        self.charge_sound_played = False
        self.blast_sound_played = False
        self.petrify_sound_played = False

    def update(self, delta_time):
        self.elapsed += delta_time

        # Phase 1: Charge (0.0-0.4s)
        if self.elapsed < 0.4:
            if not self.charge_sound_played:
                self.charge_sound_played = True
                play_sound("topiary_breath_charge")
            if self.elapsed < delta_time * 2 and self.screen_shake:
                self.screen_shake(2, 0.3)

        # Phase 2: Cone blast (0.4-1.0s)
        elif self.elapsed < 1.0:
            if not self.blast_sound_played:
                self.blast_sound_played = True
                play_sound("topiary_breath_blast")
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
            if not self.petrify_sound_played:
                self.petrify_sound_played = True
                play_sound("topiary_breath_petrify")
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
# DISSONANCE — Terrain shatter with 8-directional shrapnel
# ============================================================================

class DissonanceAnimation:
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
        self.is_upgraded = False
        self.whirl_tiles = []
        self.whirl_dest_grids = set()
        self.hidden_tiles = set()
        self.whirl_started = False
        self.whirl_shrapnel_created = False
        self.whirl_suction_done = False
        self.whirl_landing_done = False
        self.whirl_tile_data = []
        self._whirl_arc_t = 0.0
        self._whirl_landing_t = 0.0
        if game_unit:
            litho_data = getattr(game_unit, 'last_dissonance_data', None)
            if litho_data:
                self.is_topiary = litho_data.get('was_topiary', False)
                self.is_upgraded = litho_data.get('is_upgraded', False)

                if self.is_upgraded and camera:
                    for tile_info in litho_data.get('rotated_tiles', []):
                        fy, fx = tile_info['from']
                        ry, rx = tile_info['to']
                        self.whirl_tiles.append({
                            'from_screen': camera.grid_to_screen(fx, fy, centered=True),
                            'to_screen': camera.grid_to_screen(rx, ry, centered=True),
                        })
                        self.whirl_dest_grids.add((rx, ry))

                    # Precompute arc geometry for each whirl tile
                    for tile in self.whirl_tiles:
                        fsx, fsy = tile['from_screen']
                        tsx, tsy = tile['to_screen']
                        from_angle = math.atan2(fsy - self.target_y, fsx - self.target_x)
                        to_angle = math.atan2(tsy - self.target_y, tsx - self.target_x)
                        from_radius = math.hypot(fsx - self.target_x, fsy - self.target_y)
                        to_radius = math.hypot(tsx - self.target_x, tsy - self.target_y)
                        # Ensure CCW sweep (decreasing angle in screen coords)
                        if to_angle >= from_angle:
                            to_angle -= math.tau
                        self.whirl_tile_data.append({
                            'from_angle': from_angle,
                            'to_angle': to_angle,
                            'from_radius': from_radius,
                            'to_radius': to_radius,
                            'from_screen': tile['from_screen'],
                            'to_screen': tile['to_screen'],
                            'size_factor': random.uniform(0.35, 0.5),
                            'color': random.choice([STONE_GRAY, BONE_IVORY, DARK_METAL, TOPIARY_GRAY]),
                            'border_color': random.choice([BURGUNDY_LIGHT, BURGUNDY]),
                            'rotation': random.uniform(0, math.tau),
                            'landed': False,
                        })

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
        self.flight_sound_played = False

        # Crack lines for internal shatter effect
        self.cracks = []

        # Phase timing — adjusted for upgrade whirl phase
        self.flight_end = 0.9
        self.impact_end = 1.15
        self.shatter_end = 1.45
        if self.is_upgraded and self.whirl_tiles:
            self.whirl_end = 2.30
            self.shrapnel_end = 2.95
            self.total_duration = 3.05
        else:
            self.whirl_end = self.shatter_end  # No whirl phase
            self.shrapnel_end = 2.1
            self.total_duration = 2.2

    def update(self, delta_time):
        self.elapsed += delta_time

        # Phase 1: Flight — gyre projectile flies straight to target (0.0-0.9s)
        if self.elapsed < self.flight_end:
            if not self.flight_sound_played:
                self.flight_sound_played = True
                play_sound("dissonance_flight")
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
                play_sound("dissonance_impact")
                if self.screen_shake:
                    self.screen_shake(5, 0.2)
                if self.particle_emitter:
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, BURGUNDY, count=15)
                    self.particle_emitter.emit_burst(self.target_x, self.target_y, QUARTZ_PALE, count=8)
                # Generate crack lines radiating from center (scaled to AoE)
                aoe_r = 2 * TILE_SIZE + TILE_SIZE // 2
                num_cracks = 6 if not self.is_topiary else 8
                for i in range(num_cracks):
                    angle = (math.tau / num_cracks) * i + random.uniform(-0.2, 0.2)
                    length = random.uniform(aoe_r * 0.5, aoe_r * 0.95)
                    self.cracks.append({
                        'angle': angle, 'length': length,
                        'width': random.randint(1, 3),
                    })

        # Phase 3: Internal shatter — cracks widen, terrain explodes
        elif self.elapsed < self.shatter_end:
            if not self.shatter_triggered:
                self.shatter_triggered = True
                play_sound("dissonance_shatter")
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

                # Create 8-directional shrapnel (delayed if upgraded — fires after whirl)
                if not self.is_upgraded:
                    play_sound("dissonance_shrapnel")
                    self._create_shrapnel()

                # Upgraded: hide destination tiles during whirl
                if self.is_upgraded and self.whirl_tiles:
                    self.hidden_tiles.update(self.whirl_dest_grids)

        # Phase 3.5 (upgraded): Terrain whirl — tiles arc CCW around impact
        elif self.is_upgraded and self.elapsed < self.whirl_end:
            whirl_t = (self.elapsed - self.shatter_end) / (self.whirl_end - self.shatter_end)

            # Sub-phase boundaries (normalized)
            SUCTION_END = 0.21
            ARC_END = 0.76

            # --- Suction (0.00 - 0.21): gathering energy ---
            if whirl_t < SUCTION_END:
                if not self.whirl_started:
                    self.whirl_started = True
                    if self.screen_shake:
                        self.screen_shake(3, 0.15)

                suction_t = whirl_t / SUCTION_END

                # Inward-spiraling dust particles gathering toward center
                if self.particle_emitter:
                    if random.random() < 0.6 + 0.3 * suction_t:
                        angle = random.uniform(0, math.tau)
                        dist = TILE_SIZE * (3.0 - 1.0 * suction_t)
                        px = self.target_x + math.cos(angle) * dist
                        py = self.target_y + math.sin(angle) * dist
                        self.particle_emitter.emit_trail(px, py,
                            random.choice([STONE_GRAY, BURGUNDY_DARK, BONE_IVORY]), count=1)

                # Flash + shake at end of suction to announce the whirl
                if suction_t > 0.95 and not self.whirl_suction_done:
                    self.whirl_suction_done = True
                    play_sound("dissonance_whirl")
                    if self.screen_shake:
                        self.screen_shake(7, 0.5)
                    if self.screen_flash:
                        self.screen_flash(BURGUNDY_DARK, 0.12)

            # --- Arc (0.21 - 0.76): tiles fly along curved CCW paths ---
            elif whirl_t < ARC_END:
                arc_t_raw = (whirl_t - SUCTION_END) / (ARC_END - SUCTION_END)
                # Cubic ease-in-out
                if arc_t_raw < 0.5:
                    self._whirl_arc_t = 4 * arc_t_raw * arc_t_raw * arc_t_raw
                else:
                    self._whirl_arc_t = 1 - pow(-2 * arc_t_raw + 2, 3) / 2

                # Spin each tile block visually
                for td in self.whirl_tile_data:
                    td['rotation'] += (5 + 10 * self._whirl_arc_t) * delta_time

                # Trail particles along the arc
                if self.particle_emitter:
                    for td in self.whirl_tile_data:
                        if random.random() < 0.4:
                            cur_angle = td['from_angle'] + (td['to_angle'] - td['from_angle']) * self._whirl_arc_t
                            cur_radius = td['from_radius'] + (td['to_radius'] - td['from_radius']) * self._whirl_arc_t
                            px = self.target_x + math.cos(cur_angle) * cur_radius
                            py = self.target_y + math.sin(cur_angle) * cur_radius
                            self.particle_emitter.emit_trail(px, py,
                                random.choice([BURGUNDY, STONE_GRAY, BURGUNDY_DARK]), count=1)

            # --- Landing (0.76 - 1.0): tiles slam into destination ---
            else:
                self._whirl_arc_t = 1.0
                self._whirl_landing_t = (whirl_t - ARC_END) / (1.0 - ARC_END)

                if not self.whirl_landing_done:
                    self.whirl_landing_done = True
                    # Reveal destination tiles
                    self.hidden_tiles.difference_update(self.whirl_dest_grids)
                    self.whirl_dest_grids.clear()

                    # Impact effects at each landing point
                    if self.screen_shake:
                        self.screen_shake(8, 0.2)
                    if self.screen_flash:
                        self.screen_flash(QUARTZ_BRIGHT, 0.08)

                    for td in self.whirl_tile_data:
                        td['landed'] = True
                        lx, ly = td['to_screen']
                        if self.particle_emitter:
                            self.particle_emitter.emit_burst(lx, ly, STONE_GRAY, count=8)
                            self.particle_emitter.emit_burst(lx, ly, BURGUNDY, count=4)

                # Create shrapnel near end of landing
                if not self.whirl_shrapnel_created and whirl_t > 0.9:
                    self.whirl_shrapnel_created = True
                    play_sound("dissonance_shrapnel")
                    self._create_shrapnel()

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

    def _create_shrapnel(self):
        """Create 8-directional shrapnel pieces from impact point."""
        speed = TILE_SIZE * 4.5
        directions = [(-1, 0), (-1, 1), (0, 1), (1, 1),
                      (1, 0), (1, -1), (0, -1), (-1, -1)]
        for sdy, sdx in directions:
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

            # Expanding shatter burst — sized to match shrapnel AoE diameter
            aoe_r = 2 * TILE_SIZE + TILE_SIZE // 2  # shrapnel range 2 + half center tile
            burst_r = int(8 + (aoe_r - 8) * shatter_t)
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

        # Phase 3.5 (upgraded): Terrain whirl — tiles arc CCW with vortex backdrop
        if self.is_upgraded and self.whirl_tile_data and self.shatter_end <= self.elapsed < self.whirl_end:
            whirl_t = (self.elapsed - self.shatter_end) / (self.whirl_end - self.shatter_end)

            SUCTION_END = 0.21
            ARC_END = 0.76

            tx, ty = int(self.target_x), int(self.target_y)

            # --- Vortex intensity envelope ---
            if whirl_t < SUCTION_END:
                vortex_intensity = whirl_t / SUCTION_END
            elif whirl_t < ARC_END:
                vortex_intensity = 1.0
            else:
                vortex_intensity = max(0, (1 - whirl_t) / (1 - ARC_END))

            hurricane_r = TILE_SIZE * 2.5
            if whirl_t < SUCTION_END:
                base_angle = -(whirl_t * math.tau * 0.5)
            else:
                base_angle = -(whirl_t * math.tau * 2.0)

            # --- Layer 1: Background vortex atmosphere (reduced) ---
            fill_alpha = int(30 * vortex_intensity)
            if fill_alpha > 0:
                pygame.draw.circle(overlay, (*BURGUNDY_DARK, fill_alpha),
                                 (tx, ty), int(hurricane_r))

            outer_ring_alpha = int(80 * vortex_intensity)
            ring_width = max(2, int(hurricane_r * 0.04))
            if outer_ring_alpha > 0:
                pygame.draw.circle(overlay, (*BURGUNDY_LIGHT, outer_ring_alpha),
                                 (tx, ty), int(hurricane_r), ring_width)

            # 4 subtle spinning blade arcs
            num_blades = 4
            blade_span = math.radians(35)
            blade_w = max(2, int(hurricane_r * 0.04))
            for i in range(num_blades):
                blade_angle = base_angle + (math.tau / num_blades) * i
                a1 = blade_angle - blade_span / 2
                a2 = blade_angle + blade_span / 2
                pts = []
                for step in range(10):
                    t_step = a1 + (a2 - a1) * step / 9
                    pts.append((int(tx + math.cos(t_step) * hurricane_r),
                               int(ty + math.sin(t_step) * hurricane_r)))
                if len(pts) >= 2:
                    blade_alpha = int(100 * vortex_intensity)
                    pygame.draw.lines(overlay, (*QUARTZ_PALE, blade_alpha),
                                     False, pts, blade_w)

            # Faint radial spokes
            num_spokes = 6
            spoke_alpha = int(25 * vortex_intensity)
            if spoke_alpha > 0:
                inner_spoke_r = TILE_SIZE * 0.4
                for i in range(num_spokes):
                    spoke_a = base_angle * 0.5 + (math.tau / num_spokes) * i
                    sx1 = tx + math.cos(spoke_a) * inner_spoke_r
                    sy1 = ty + math.sin(spoke_a) * inner_spoke_r
                    sx2 = tx + math.cos(spoke_a) * hurricane_r * 0.9
                    sy2 = ty + math.sin(spoke_a) * hurricane_r * 0.9
                    pygame.draw.line(overlay, (*BURGUNDY_DARK, spoke_alpha),
                                   (int(sx1), int(sy1)), (int(sx2), int(sy2)), 1)

            # Eye core
            eye_r = max(4, int(TILE_SIZE * 0.2))
            eye_pulse = 0.7 + 0.3 * math.sin(whirl_t * math.pi * 5)
            eye_alpha = int(140 * vortex_intensity * eye_pulse)
            if eye_alpha > 0:
                pygame.draw.circle(overlay, (*QUARTZ_PALE, min(255, eye_alpha)),
                                 (tx, ty), eye_r)
                pygame.draw.circle(overlay, (*BONE_IVORY, min(255, int(eye_alpha * 0.8))),
                                 (tx, ty), max(2, eye_r - 2))

            # --- Layer 2: Suction — tiles tremble at source positions ---
            if whirl_t < SUCTION_END:
                suction_t = whirl_t / SUCTION_END
                for td in self.whirl_tile_data:
                    fsx, fsy = td['from_screen']
                    # Increasing tremble
                    tremble = 1 + 3 * suction_t
                    ox = math.sin(self.elapsed * 40 + td['from_angle'] * 3) * tremble
                    oy = math.cos(self.elapsed * 47 + td['from_angle'] * 5) * tremble
                    bx, by = fsx + ox, fsy + oy
                    block_size = int(TILE_SIZE * td['size_factor'])
                    bhs = block_size // 2

                    block_alpha = int(200 - 60 * suction_t)
                    pygame.draw.rect(overlay, (*td['color'], block_alpha),
                                   (int(bx - bhs), int(by - bhs), block_size, block_size))
                    pygame.draw.rect(overlay, (*td['border_color'], int(160 * (1 - 0.3 * suction_t))),
                                   (int(bx - bhs), int(by - bhs), block_size, block_size), 2)

                    # Burgundy resonance glow intensifying
                    glow_alpha = int(40 + 80 * suction_t)
                    glow_r = int(block_size * 0.7 + block_size * 0.3 * suction_t)
                    pygame.draw.circle(overlay, (*BURGUNDY, glow_alpha),
                                     (int(bx), int(by)), glow_r)

            # --- Layer 3: Arc flight — tiles fly along curved CCW paths ---
            elif whirl_t < ARC_END:
                arc_t = self._whirl_arc_t
                for td in self.whirl_tile_data:
                    cur_angle = td['from_angle'] + (td['to_angle'] - td['from_angle']) * arc_t
                    cur_radius = td['from_radius'] + (td['to_radius'] - td['from_radius']) * arc_t
                    bx = self.target_x + math.cos(cur_angle) * cur_radius
                    by = self.target_y + math.sin(cur_angle) * cur_radius

                    block_size = int(TILE_SIZE * td['size_factor'])
                    bhs = block_size // 2

                    # Motion trail — faint afterimage at earlier arc position
                    trail_arc_t = max(0, arc_t - 0.12)
                    trail_angle = td['from_angle'] + (td['to_angle'] - td['from_angle']) * trail_arc_t
                    trail_radius = td['from_radius'] + (td['to_radius'] - td['from_radius']) * trail_arc_t
                    trail_x = self.target_x + math.cos(trail_angle) * trail_radius
                    trail_y = self.target_y + math.sin(trail_angle) * trail_radius
                    trail_corners = []
                    trail_rot = td['rotation'] - 0.5
                    for ci in range(4):
                        ca = trail_rot + ci * math.pi / 2
                        trail_corners.append((
                            int(trail_x + math.cos(ca) * bhs * 0.7),
                            int(trail_y + math.sin(ca) * bhs * 0.7),
                        ))
                    pygame.draw.polygon(overlay, (*BURGUNDY_DARK, 50), trail_corners)

                    # Burgundy glow envelope
                    pygame.draw.circle(overlay, (*BURGUNDY, 35),
                                     (int(bx), int(by)), int(block_size * 0.8))

                    # Spinning terrain block (rotated polygon)
                    rot = td['rotation']
                    corners = []
                    for ci in range(4):
                        ca = rot + ci * math.pi / 2
                        corners.append((
                            int(bx + math.cos(ca) * bhs * 0.9),
                            int(by + math.sin(ca) * bhs * 0.9),
                        ))
                    pygame.draw.polygon(overlay, (*td['color'], 210), corners)
                    pygame.draw.polygon(overlay, (*td['border_color'], 170), corners, 2)

            # --- Layer 4: Landing — impact flashes at destinations ---
            else:
                landing_t = self._whirl_landing_t
                for td in self.whirl_tile_data:
                    dx, dy = td['to_screen']

                    # Expanding ring flash
                    if landing_t < 0.5:
                        flash_t = landing_t / 0.5
                        flash_r = int(8 + 20 * flash_t)
                        flash_alpha = int(200 * (1 - flash_t))
                        if flash_alpha > 0:
                            pygame.draw.circle(overlay, (*QUARTZ_BRIGHT, flash_alpha),
                                             (int(dx), int(dy)), flash_r, max(2, flash_r // 4))
                            pygame.draw.circle(overlay, (*BURGUNDY, int(flash_alpha * 0.5)),
                                             (int(dx), int(dy)), int(flash_r * 0.6))

                    # Dust puff
                    if landing_t < 0.7:
                        dust_t = landing_t / 0.7
                        dust_r = int(5 + 15 * dust_t)
                        dust_alpha = int(60 * (1 - dust_t))
                        if dust_alpha > 0:
                            pygame.draw.circle(overlay, (*STONE_GRAY, dust_alpha),
                                             (int(dx), int(dy)), dust_r)

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
