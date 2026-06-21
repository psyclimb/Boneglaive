#!/usr/bin/env python3
"""
Graphical animations for the ORDNANCE GRAFT unit type and its ORDNANCE DRONE summon.
Skill animations with particles, screen effects, and phased sequencing.

Color scheme matches the ORDNANCE GRAFT sprite: olive drab, gunmetal, black spiked
bombs ("bolas"), and an amber fuse/ember accent.
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
# ORDNANCE GRAFT COLOR PALETTE
# ============================================================================

OLIVE = (75, 83, 32)
OLIVE_DARK = (47, 54, 20)
OLIVE_LIGHT = (107, 122, 58)
GUNMETAL = (74, 74, 79)
GUNMETAL_DARK = (58, 58, 63)
GUNMETAL_LIGHT = (138, 138, 142)
BOMB_BLACK = (26, 26, 20)
BOMB_EDGE = (58, 58, 42)
TAN = (194, 178, 128)
AMBER = (255, 140, 58)
AMBER_BRIGHT = (255, 208, 138)
AMBER_DARK = (194, 84, 26)
SMOKE = (90, 90, 86)


# ============================================================================
# Shared helpers
# ============================================================================

def _spiked_ball_points(cx, cy, outer, rot=0.0, pts=11, inner_ratio=0.6):
    """Return the polygon points of a spiked ball (his bola motif) for pygame.draw."""
    P = []
    for k in range(pts * 2):
        r = outer if k % 2 == 0 else outer * inner_ratio
        a = math.radians(rot + k * 180.0 / pts)
        P.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return P


def _draw_spiked_bomb(overlay, cx, cy, outer, alpha, rot=0.0):
    """Draw a black spiked bomb with an amber-edged body onto an SRCALPHA overlay."""
    pts = _spiked_ball_points(cx, cy, outer, rot)
    pygame.draw.polygon(overlay, (*BOMB_BLACK, alpha), pts)
    pygame.draw.polygon(overlay, (*BOMB_EDGE, alpha), pts, 1)
    pygame.draw.circle(overlay, (*BOMB_BLACK, alpha), (int(cx), int(cy)), int(outer * 0.55))


def _grid_center(camera, gy, gx):
    """Grid (y, x) -> screen pixel center. Camera takes (grid_x, grid_y)."""
    if camera:
        return camera.grid_to_screen(gx, gy, centered=True)
    return (gx * TILE_SIZE + TILE_SIZE // 2, gy * TILE_SIZE + TILE_SIZE // 2)


# ============================================================================
# INOCULANT — linstock strike that plants a single spiked bola, amber spark
# ============================================================================

class InoculantAnimation:
    """A quick linstock jab: amber spark on the target, then a spiked bomb thunks on."""

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.total_duration = 0.55
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback

        # Resolve target screen position (the unit that got grafted).
        if target_pos is not None:
            self.tx, self.ty = _grid_center(camera, target_pos[0], target_pos[1])
        elif target_unit is not None:
            gu = getattr(target_unit, 'game_unit', target_unit)
            self.tx, self.ty = _grid_center(camera, gu.y, gu.x)
        else:
            self.tx, self.ty = _grid_center(camera, caster_unit.game_unit.y, caster_unit.game_unit.x)

        self.spark_done = False
        self.bomb_rot = random.uniform(0, 60)

    def update(self, delta_time):
        self.elapsed += delta_time

        # Impact spark at ~0.1s. (The skill's primary sound is played by the factory
        # via SKILL_SOUNDS when this animation is created — don't double it here.)
        if not self.spark_done and self.elapsed > 0.1:
            self.spark_done = True
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=10)
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER_BRIGHT, count=5)
                self.particle_emitter.emit_burst(self.tx, self.ty, BOMB_BLACK, count=4)
            if self.screen_shake:
                self.screen_shake(3, 0.12)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Amber spark flash (fades fast).
        if self.elapsed > 0.1:
            st = min(1.0, (self.elapsed - 0.1) / 0.18)
            flash_alpha = max(0, int(180 * (1 - st)))
            if flash_alpha > 0:
                pygame.draw.circle(overlay, (*AMBER, flash_alpha), (int(self.tx), int(self.ty)), int(6 + st * 8))
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, flash_alpha), (int(self.tx), int(self.ty)), int(3 + st * 4))

        # The planted bomb settles in (scales up + slight jiggle).
        if self.elapsed > 0.12:
            bt = min(1.0, (self.elapsed - 0.12) / 0.25)
            ease = 1 - (1 - bt) * (1 - bt)
            size = 5 * ease
            jiggle = math.sin(self.elapsed * 40) * (1 - bt) * 2
            bomb_alpha = int(255 * min(1.0, self.elapsed / 0.2))
            if size > 0.5:
                _draw_spiked_bomb(overlay, self.tx + jiggle, self.ty, size, bomb_alpha, self.bomb_rot)

        surface.blit(overlay, (0, 0))


# ============================================================================
# SKYHOOK — the drone yanks him up by a cable, hauls him over swinging, drops him
# in an arrival slam. Theatric, Vault-style: it MOVES the graft's actual sprite
# (caster.x/y + wind_up_rotation) while drawing the cable/hook/drone overlay.
# ============================================================================

class SkyhookAnimationController:
    """Aerial extraction: a sharp upward YANK, a high suspended CARRY (the body swings
    like a pendulum on the cable, a drone silhouette leading above), then a DROP + slam.
    Drives the caster AnimatedUnit's position/rotation like VaultAnimationController."""

    # phase boundaries (fractions of total_duration)
    YANK_END = 0.18
    CARRY_END = 0.74
    TOTAL = 0.95

    def __init__(self, caster_unit, target_pos, particle_emitter, screen_shake_callback, camera=None):
        self.caster = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback or (lambda i, d: None)
        self.camera = camera
        self.active = True
        self.elapsed = 0.0

        # Origin = where the sprite currently is (the visual hasn't moved yet).
        self.ox, self.oy = caster_unit.x, caster_unit.y
        # Destination screen pos. target_pos is (grid_y, grid_x) from the renderer.
        tgy, tgx = target_pos
        if camera:
            self.dx, self.dy = camera.grid_to_screen(tgx, tgy, centered=True)
        else:
            self.dx = 100 + tgx * TILE_SIZE + TILE_SIZE // 2
            self.dy = 50 + tgy * TILE_SIZE + TILE_SIZE // 2
        self.dest_grid = (tgx, tgy)

        self.arc_height = 150          # how high the lift carries him (he's hauled UP)
        self.slam_done = False
        self.launch_done = False

        # set up sprite-rotation state (the renderer reads wind_up_rotation)
        self.caster.wind_up_rotation = 0

        # Launch beat: cable snaps taut, dust kicks up at the origin.
        if self.particle_emitter:
            for _ in range(14):
                a = random.uniform(0, math.tau)
                sp = random.uniform(40, 110)
                p = Particle(self.ox, self.oy + 14, math.cos(a) * sp, math.sin(a) * sp - 40,
                             random.choice((SMOKE, TAN)), random.uniform(3, 6), random.uniform(0.4, 0.7))
                p.gravity = 120
                self.particle_emitter.particles.append(p)

    def update(self, delta_time):
        if not self.active:
            return False
        self.elapsed += delta_time
        t = min(1.0, self.elapsed / self.TOTAL)

        if t < self.YANK_END:
            # YANK: snatched sharply upward, almost no horizontal travel yet.
            yt = t / self.YANK_END
            ease = yt * yt  # accelerate up
            self.caster.x = self.ox
            self.caster.y = self.oy - self.arc_height * 0.55 * ease
            self.caster.wind_up_rotation = math.sin(yt * math.pi) * 8  # tiny destabilized tilt

        elif t < self.CARRY_END:
            # CARRY: hauled across, suspended high, swinging like a pendulum on the line.
            ct = (t - self.YANK_END) / (self.CARRY_END - self.YANK_END)
            ease = 1 - (1 - ct) * (1 - ct)  # ease-out horizontal glide
            self.caster.x = self.ox + (self.dx - self.ox) * ease
            # stays high: blend the yank height into a lifted arc that dips toward the end
            lift = self.arc_height * (0.55 + 0.45 * math.sin(min(1.0, ct * 1.1) * math.pi))
            self.caster.y = (self.oy + (self.dy - self.oy) * ease) - lift
            # damped pendulum sway (dangling on the cable), NOT a flip
            self.caster.wind_up_rotation = math.sin(ct * math.pi * 3) * 18 * (1 - ct * 0.5)
            # rotor-wash trail from the drone above
            if self.particle_emitter and random.random() < 0.4:
                self.particle_emitter.emit_trail(self.caster.x + random.uniform(-6, 6),
                                                 self.caster.y - 30, GUNMETAL_LIGHT, count=1)

        elif not self.slam_done:
            # DROP + SLAM: cable releases, he falls the last bit and hits the tile hard.
            dt = (t - self.CARRY_END) / (1.0 - self.CARRY_END)
            fall = dt * dt  # accelerate down
            # final descent from carry height to the ground
            self.caster.x = self.dx
            self.caster.y = (self.dy - self.arc_height * 0.25) + (self.arc_height * 0.25) * fall
            self.caster.wind_up_rotation = (1 - dt) * 10  # straighten on landing

            if dt >= 0.85:
                # touchdown — fire the slam
                self.slam_done = True
                self.caster.x, self.caster.y = self.dx, self.dy
                self.caster.wind_up_rotation = 0
                self._slam()

        if self.elapsed >= self.TOTAL:
            self.caster.x, self.caster.y = self.dx, self.dy
            self.caster.wind_up_rotation = 0
            self.active = False
        return self.active

    def _slam(self):
        play_sound("skyhook_land")
        self.screen_shake(8, 0.25)
        pe = self.particle_emitter
        if not pe:
            return
        lx, ly = self.dx, self.dy
        pe.emit_burst(lx, ly, AMBER, count=20)
        pe.emit_burst(lx, ly, AMBER_BRIGHT, count=10)
        pe.emit_burst(lx, ly, BOMB_BLACK, count=10)
        # outward dust ring on the slam
        for _ in range(18):
            a = random.uniform(0, math.tau)
            sp = random.uniform(70, 150)
            p = Particle(lx, ly + 10, math.cos(a) * sp, math.sin(a) * sp - 20,
                         random.choice((SMOKE, TAN, (70, 70, 66))), random.uniform(4, 8), random.uniform(0.5, 0.9))
            p.gravity = 140
            pe.particles.append(p)
        # a few amber graft-pops on the 8 surrounding tiles (the AoE arrival graft)
        for k in range(8):
            ang = math.radians(k * 45)
            gx = lx + math.cos(ang) * TILE_SIZE
            gy = ly + math.sin(ang) * TILE_SIZE
            pe.emit_burst(gx, gy, AMBER, count=3)

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        t = min(1.0, self.elapsed / self.TOTAL)

        # While airborne (yank + carry + drop, before the slam), draw the cable + hook
        # attached to the graft trailing up to a drone silhouette leading above.
        if not self.slam_done:
            cx, cy = self.caster.x, self.caster.y
            # the drone hovers above and slightly ahead of him along the travel direction
            lead = 0.0
            if t > self.YANK_END:
                lead = TILE_SIZE * 0.5  # leads forward during the carry
            dir_x = 1 if self.dx >= self.ox else -1
            drone_x = cx + dir_x * lead * (1 if t < self.CARRY_END else 0)
            drone_y = cy - TILE_SIZE * 1.7

            # cable (gunmetal, taut) from the drone down to a hook on his harness
            hook_x, hook_y = cx, cy - 8
            pygame.draw.line(overlay, (*GUNMETAL_DARK, 230), (int(drone_x), int(drone_y)),
                             (int(hook_x), int(hook_y)), 3)
            pygame.draw.line(overlay, (*GUNMETAL_LIGHT, 150), (int(drone_x), int(drone_y)),
                             (int(hook_x), int(hook_y)), 1)
            # grappling hook flukes at his harness
            pygame.draw.line(overlay, (*GUNMETAL, 235), (int(hook_x), int(hook_y)),
                             (int(hook_x - 5), int(hook_y + 6)), 3)
            pygame.draw.line(overlay, (*GUNMETAL, 235), (int(hook_x), int(hook_y)),
                             (int(hook_x + 5), int(hook_y + 6)), 3)

            # stylized drone silhouette (X-frame quad) above, leading the haul
            self._draw_drone(overlay, drone_x, drone_y, t)

        # The slam shockwave ring at the landing.
        if self.slam_done:
            st = min(1.0, (self.elapsed - self.CARRY_END) / (self.TOTAL - self.CARRY_END))
            ring_r = int(TILE_SIZE * 0.4 + st * TILE_SIZE * 1.7)
            ring_a = max(0, int(210 * (1 - st)))
            if ring_a > 0:
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, ring_a), (int(self.dx), int(self.dy)), ring_r, 3)
                pygame.draw.circle(overlay, (*AMBER, max(0, ring_a - 70)),
                                   (int(self.dx), int(self.dy)), int(ring_r * 0.65), 2)
            core_a = max(0, int(180 * (1 - st)))
            if core_a > 0:
                pygame.draw.circle(overlay, (*AMBER, core_a), (int(self.dx), int(self.dy)), int(10 * (1 - st) + 3))

        surface.blit(overlay, (0, 0))

    def _draw_drone(self, overlay, dx, dy, t):
        """A small top-down X-frame quad silhouette with spinning-rotor blur."""
        r = TILE_SIZE * 0.30
        # body
        pygame.draw.circle(overlay, (*OLIVE, 235), (int(dx), int(dy)), int(r * 0.5))
        pygame.draw.circle(overlay, (*GUNMETAL_DARK, 235), (int(dx), int(dy)), int(r * 0.3))
        # 4 arms to rotor blurs
        for ang in (45, 135, 225, 315):
            a = math.radians(ang)
            rx, ry = dx + math.cos(a) * r, dy + math.sin(a) * r
            pygame.draw.line(overlay, (*OLIVE_DARK, 230), (int(dx), int(dy)), (int(rx), int(ry)), 3)
            # rotor disc (translucent blur, brighter alpha flicker)
            blur_a = 90 + int(40 * math.sin(self.elapsed * 50 + ang))
            pygame.draw.circle(overlay, (*GUNMETAL_LIGHT, blur_a), (int(rx), int(ry)), int(r * 0.42), 1)
        # amber sensor nub (front)
        pygame.draw.circle(overlay, (*AMBER, 235), (int(dx), int(dy - r * 0.5)), 2)


# ============================================================================
# HARVEST — field-wide bola detonation. The showpiece.
# ============================================================================

class HarvestAnimation:
    """He touches off every fused bola at once: amber detonation bursts and gunmetal
    shrapnel radiate from each bola'd enemy, with a heavy shake + flash."""

    # Per-blast detonation timing: each point ignites briefly then erupts. Points are
    # staggered slightly so multiple bombs read as a chaotic chain, not one blip.
    IGNITE_AT = 0.18          # when the warm-up glow peaks / blast fires (base)
    BLAST_DUR = 0.70          # how long a single fireball lives after it fires

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        # NOTE: deliberately no screen_flash — no full-screen flashes on this unit.

        # The detonation tiles are recorded by HarvestSkill.execute() into
        # last_harvest_data BEFORE the bolas are consumed — read them from there (the
        # live bolas lists are already cleared by the time this animation runs).
        self.blasts = []  # list of dicts: {x, y, t0, fired, seed}
        caster_gu = caster_unit.game_unit
        harvest_data = getattr(caster_gu, 'last_harvest_data', None)
        targets = []
        if harvest_data and harvest_data.get('detonations'):
            targets = [(y, x) for (y, x, _stacks) in harvest_data['detonations']]
        if not targets:
            targets.append((caster_gu.y, caster_gu.x))  # fallback so something shows
        for i, (gy, gx) in enumerate(targets):
            bx, by = _grid_center(camera, gy, gx)
            self.blasts.append({
                'x': bx, 'y': by,
                't0': self.IGNITE_AT + random.uniform(0.0, 0.10),  # stagger
                'fired': False,
                'seed': random.uniform(0, math.tau),
            })

        # Total duration = the last blast's fire time + its lifetime.
        self.total_duration = max(b['t0'] for b in self.blasts) + self.BLAST_DUR
        self.shake_done = False

    def _erupt(self, b):
        """Spawn the heavy layered particle burst for one blast point."""
        bx, by = b['x'], b['y']
        pe = self.particle_emitter
        if not pe:
            return
        # Fast spark layers (amber + white-hot) — the bright outward flash debris.
        pe.emit_burst(bx, by, AMBER_BRIGHT, count=22)
        pe.emit_burst(bx, by, AMBER, count=26)
        pe.emit_burst(bx, by, (255, 255, 255), count=10)
        # Heavy high-velocity gunmetal shrapnel (hand-rolled: fast, gravity, bigger).
        for _ in range(18):
            a = random.uniform(0, math.tau)
            sp = random.uniform(140, 280)
            p = Particle(bx, by, math.cos(a) * sp, math.sin(a) * sp,
                         random.choice((GUNMETAL_LIGHT, GUNMETAL)),
                         random.uniform(2.0, 4.0), random.uniform(0.4, 0.9))
            p.gravity = 320
            pe.particles.append(p)
        # Dark spiked-bomb fragments blown apart (bola motif shattering).
        for _ in range(12):
            a = random.uniform(0, math.tau)
            sp = random.uniform(90, 200)
            p = Particle(bx, by, math.cos(a) * sp, math.sin(a) * sp,
                         BOMB_BLACK, random.uniform(2.0, 4.5), random.uniform(0.5, 1.0))
            p.gravity = 280
            pe.particles.append(p)
        # Rising smoke that lingers (upward drift, long-lived, no gravity).
        for _ in range(14):
            a = random.uniform(0, math.tau)
            sp = random.uniform(20, 60)
            p = Particle(bx + random.uniform(-8, 8), by + random.uniform(-8, 8),
                         math.cos(a) * sp, math.sin(a) * sp - random.uniform(30, 70),
                         random.choice((SMOKE, (70, 70, 66))),
                         random.uniform(4.0, 7.0), random.uniform(0.9, 1.6))
            p.gravity = -10
            pe.particles.append(p)

    def update(self, delta_time):
        self.elapsed += delta_time

        any_fired_now = False
        for b in self.blasts:
            if not b['fired'] and self.elapsed >= b['t0']:
                b['fired'] = True
                any_fired_now = True
                self._erupt(b)

        # Screen shake scales with how many bombs are going off (more = bigger).
        if any_fired_now and self.screen_shake:
            n = len(self.blasts)
            self.screen_shake(min(14, 7 + n * 2), 0.35)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def _draw_fireball(self, overlay, bx, by, t, seed):
        """A billowing, expanding fireball: layered filled circles from white-hot core
        out to dark smoke, punching out fast (ease-out) then dissipating."""
        # Expansion eases out fast; the visible blast is biggest early then fades.
        ease = 1 - (1 - t) * (1 - t) * (1 - t)         # cubic ease-out for radius
        fade = max(0.0, 1.0 - t)                        # overall opacity falloff
        base_r = TILE_SIZE * (0.35 + ease * 1.15)       # grows up to ~1.5 tiles

        # Layers: (radius_factor, color, base_alpha). Outer/cooler first, hot core last.
        layers = [
            (1.00, SMOKE, 70),
            (0.85, AMBER_DARK, 150),
            (0.65, AMBER, 210),
            (0.45, AMBER_BRIGHT, 235),
            (0.26, (255, 255, 255), 250),
        ]
        for j, (rf, col, a0) in enumerate(layers):
            alpha = int(a0 * fade)
            if alpha <= 0:
                continue
            # a little per-layer jitter so the ball reads as billowing, not concentric.
            jx = math.cos(seed + j * 1.3) * base_r * 0.10 * (1 - t)
            jy = math.sin(seed + j * 1.7) * base_r * 0.10 * (1 - t)
            r = int(base_r * rf)
            if r > 0:
                pygame.draw.circle(overlay, (*col, alpha), (int(bx + jx), int(by + jy)), r)

        # Bright shockwave ring racing ahead of the fireball.
        ring_r = int(TILE_SIZE * 0.3 + ease * TILE_SIZE * 1.9)
        ring_a = int(200 * max(0.0, 1.0 - t * 1.3))
        if ring_a > 0:
            pygame.draw.circle(overlay, (*AMBER_BRIGHT, ring_a), (int(bx), int(by)), ring_r, 3)

    def _draw_local_flash(self, overlay, bx, by, t):
        """A LOCAL white-hot bloom on the unit at the instant of the blast (not a
        full-screen flash) — blooms in the first ~0.12s then collapses."""
        ft = t / 0.18
        if ft > 1.0:
            return
        a = int(255 * (1 - ft))
        if a <= 0:
            return
        r = int(TILE_SIZE * (0.5 + ft * 0.6))
        pygame.draw.circle(overlay, (255, 255, 255, a), (int(bx), int(by)), r)
        pygame.draw.circle(overlay, (*AMBER_BRIGHT, a), (int(bx), int(by)), int(r * 1.3), 4)

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for b in self.blasts:
            bx, by = b['x'], b['y']
            # Pre-ignition warm-up glow building at the bomb.
            if not b['fired']:
                it = min(1.0, self.elapsed / max(0.001, b['t0']))
                ga = int(140 * it)
                pygame.draw.circle(overlay, (*AMBER, ga), (int(bx), int(by)), int(5 + it * 6))
                # a flickering hot pinpoint
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, int(ga * 1.2)),
                                   (int(bx), int(by)), int(2 + it * 2))
                continue

            # Post-blast: local flash bloom + billowing fireball.
            bt = (self.elapsed - b['t0']) / self.BLAST_DUR
            if bt > 1.0:
                continue
            self._draw_fireball(overlay, bx, by, bt, b['seed'])
            self._draw_local_flash(overlay, bx, by, bt)

        surface.blit(overlay, (0, 0))


# ============================================================================
# ORDNANCE GRAFT basic attack — a linstock pole-strike (no bomb; just a hit)
# ============================================================================

class OrdnanceGraftLinstockAttack:
    """His basic attack: a long linstock (match-staff) sweep from attacker toward the
    target, capped with an amber flick from the lit slow-match. Plants no bola — his
    basic attack is just a hit. Uses the AnimatedUnit screen positions like the other
    basic attacks (attacker_unit.x/.y are pixels)."""

    def __init__(self, attacker_unit, target_unit, particle_emitter, screen_shake_callback, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.total_duration = 0.45
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback or (lambda i, d: None)

        self.ax, self.ay = attacker_unit.x, attacker_unit.y
        if target_unit is not None:
            self.tx, self.ty = target_unit.x, target_unit.y
        else:
            self.tx, self.ty = self.ax, self.ay
        # Direction + perpendicular for the staff sweep.
        dx, dy = self.tx - self.ax, self.ty - self.ay
        dist = max(1.0, math.hypot(dx, dy))
        self.ux, self.uy = dx / dist, dy / dist
        self.impact_done = False

    def update(self, delta_time):
        self.elapsed += delta_time
        if not self.impact_done and self.elapsed > 0.18:
            self.impact_done = True
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, GUNMETAL_LIGHT, count=8)
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=5)
            self.screen_shake(4, 0.14)
        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # The staff sweeps through an arc toward the target (windup -> strike).
        t = min(1.0, self.elapsed / 0.22)
        ease = 1 - (1 - t) * (1 - t)
        # pivot near the attacker; the staff tip travels from a wound-up angle to the target
        perp_x, perp_y = -self.uy, self.ux
        windup = (1 - ease)  # 1 at windup, 0 at full extension
        reach = TILE_SIZE * 0.95
        # tip position: along the aim direction, swung in from the perpendicular at windup
        tip_x = self.ax + self.ux * reach * ease + perp_x * reach * 0.5 * windup
        tip_y = self.ay + self.uy * reach * ease + perp_y * reach * 0.5 * windup
        # butt of the staff sits just behind the attacker
        butt_x = self.ax - self.ux * (TILE_SIZE * 0.25)
        butt_y = self.ay - self.uy * (TILE_SIZE * 0.25)

        staff_alpha = int(235 * min(1.0, self.elapsed / 0.12)) if self.elapsed < 0.3 else max(0, int(235 * (1 - (self.elapsed - 0.3) / 0.15)))
        if staff_alpha > 0:
            # tan shaft + darker grain
            pygame.draw.line(overlay, (*TAN, staff_alpha), (int(butt_x), int(butt_y)), (int(tip_x), int(tip_y)), 4)
            pygame.draw.line(overlay, (*OLIVE_DARK, max(0, staff_alpha - 60)), (int(butt_x), int(butt_y)), (int(tip_x), int(tip_y)), 1)
            # gunmetal head at the tip
            pygame.draw.circle(overlay, (*GUNMETAL, staff_alpha), (int(tip_x), int(tip_y)), 4)
            pygame.draw.circle(overlay, (*GUNMETAL_LIGHT, staff_alpha), (int(tip_x), int(tip_y)), 4, 1)
            # amber slow-match ember flicking off the head
            ember_r = 2 + int(math.sin(self.elapsed * 30) * 1)
            pygame.draw.circle(overlay, (*AMBER, staff_alpha), (int(tip_x + perp_x * 5), int(tip_y + perp_y * 5)), ember_r)

        # impact spark on the target
        if self.impact_done:
            it = min(1.0, (self.elapsed - 0.18) / 0.18)
            fa = max(0, int(170 * (1 - it)))
            if fa > 0:
                pygame.draw.circle(overlay, (*AMBER, fa), (int(self.tx), int(self.ty)), int(4 + it * 6))

        surface.blit(overlay, (0, 0))


# ============================================================================
# ORDNANCE DRONE basic attack — rotor buzz + amber tracer that plants a spiked bola
# ============================================================================

class OrdnanceDroneBolaAttack:
    """The drone's basic attack: a downward rotor-buzz tracer toward the target, then a
    spiked bomb thunks on with a spark (the drone is a mobile planter). Uses AnimatedUnit
    screen positions (attacker_unit.x/.y are pixels)."""

    def __init__(self, attacker_unit, target_unit=None,
                 particle_emitter=None, screen_shake_callback=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.total_duration = 0.5
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback or (lambda i, d: None)

        self.sx, self.sy = attacker_unit.x, attacker_unit.y
        if target_unit is not None:
            self.tx, self.ty = target_unit.x, target_unit.y
        else:
            self.tx, self.ty = self.sx, self.sy

        self.fired = False
        self.impact_done = False
        self.bomb_rot = random.uniform(0, 60)

    def update(self, delta_time):
        self.elapsed += delta_time

        if not self.fired and self.elapsed > 0.02:
            self.fired = True
            play_sound("ordnance_drone_attack")
            # a little rotor-wash at the drone on fire
            if self.particle_emitter:
                self.particle_emitter.emit_trail(self.sx, self.sy, GUNMETAL_LIGHT, count=3)

        if not self.impact_done and self.elapsed > 0.18:
            self.impact_done = True
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=8)
                self.particle_emitter.emit_burst(self.tx, self.ty, BOMB_BLACK, count=4)
            self.screen_shake(2, 0.1)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Amber tracer from drone to target (during flight), with a faint twin rotor blur.
        if self.elapsed < 0.18:
            t = self.elapsed / 0.18
            hx = self.sx + (self.tx - self.sx) * t
            hy = self.sy + (self.ty - self.sy) * t
            pygame.draw.line(overlay, (*AMBER, 180), (int(self.sx), int(self.sy)), (int(hx), int(hy)), 2)
            pygame.draw.circle(overlay, (*AMBER_BRIGHT, 220), (int(hx), int(hy)), 3)
            # rotor blur at the drone
            blur_a = int(120 * (1 - t))
            if blur_a > 0:
                pygame.draw.ellipse(overlay, (*GUNMETAL_LIGHT, blur_a),
                                    (int(self.sx - 9), int(self.sy - 3), 18, 6), 1)

        # Planted bomb settles in.
        if self.elapsed > 0.18:
            bt = min(1.0, (self.elapsed - 0.18) / 0.2)
            ease = 1 - (1 - bt) * (1 - bt)
            size = 4.5 * ease
            bomb_alpha = int(255 * min(1.0, (self.elapsed - 0.18) / 0.15))
            if size > 0.5:
                _draw_spiked_bomb(overlay, self.tx, self.ty, size, bomb_alpha, self.bomb_rot)

        surface.blit(overlay, (0, 0))
