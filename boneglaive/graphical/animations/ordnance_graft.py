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
# SKYHOOK — drone cable drops, hauls him over, then an amber arrival slam
# ============================================================================

class SkyhookAnimation:
    """Cable + hook drops to the landing; lift dust; then an amber shockwave + bomb
    burst slam grafting the surrounding tiles."""

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.total_duration = 0.9
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback

        # The landing point is where the graft now is (factory prefers post-move pos).
        gu = caster_unit.game_unit
        self.lx, self.ly = _grid_center(camera, gu.y, gu.x)

        self.slam_done = False
        self.slam_t0 = 0.45  # when the slam fires

    def update(self, delta_time):
        self.elapsed += delta_time

        # (Skyhook's primary sound is played by the factory via SKILL_SOUNDS on creation.)

        # Trail of rotor-wash / lift dust during the haul.
        if self.elapsed < self.slam_t0 and self.particle_emitter and random.random() < 0.5:
            self.particle_emitter.emit_trail(
                self.lx + random.uniform(-10, 10),
                self.ly + random.uniform(-6, 6),
                SMOKE, count=1)

        # The arrival slam.
        if not self.slam_done and self.elapsed >= self.slam_t0:
            self.slam_done = True
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.lx, self.ly, AMBER, count=18)
                self.particle_emitter.emit_burst(self.lx, self.ly, AMBER_BRIGHT, count=8)
                self.particle_emitter.emit_burst(self.lx, self.ly, BOMB_BLACK, count=10)
                self.particle_emitter.emit_burst(self.lx, self.ly, SMOKE, count=8)
            if self.screen_shake:
                self.screen_shake(7, 0.22)
            if self.screen_flash:
                self.screen_flash(AMBER, 0.08)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Phase 1: cable + hook descending from above the landing.
        if self.elapsed < self.slam_t0:
            t = self.elapsed / self.slam_t0
            top_y = self.ly - TILE_SIZE * 2.2
            hook_y = top_y + (self.ly - top_y) * min(1.0, t * 1.3)
            # cable
            pygame.draw.line(overlay, (*GUNMETAL_DARK, 220), (int(self.lx), int(top_y)),
                             (int(self.lx), int(hook_y)), 3)
            pygame.draw.line(overlay, (*GUNMETAL_LIGHT, 160), (int(self.lx), int(top_y)),
                             (int(self.lx), int(hook_y)), 1)
            # hook flukes
            pygame.draw.line(overlay, (*GUNMETAL, 230), (int(self.lx), int(hook_y)),
                             (int(self.lx - 5), int(hook_y + 6)), 3)
            pygame.draw.line(overlay, (*GUNMETAL, 230), (int(self.lx), int(hook_y)),
                             (int(self.lx + 5), int(hook_y + 6)), 3)

        # Phase 2: expanding amber shockwave ring + lingering scorch.
        if self.elapsed >= self.slam_t0:
            st = min(1.0, (self.elapsed - self.slam_t0) / (self.total_duration - self.slam_t0))
            ring_r = int(TILE_SIZE * 0.4 + st * TILE_SIZE * 1.6)
            ring_alpha = max(0, int(200 * (1 - st)))
            if ring_alpha > 0:
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, ring_alpha), (int(self.lx), int(self.ly)), ring_r, 3)
                pygame.draw.circle(overlay, (*AMBER, max(0, ring_alpha - 60)),
                                   (int(self.lx), int(self.ly)), int(ring_r * 0.7), 2)
            # central flash
            core_alpha = max(0, int(170 * (1 - st)))
            if core_alpha > 0:
                pygame.draw.circle(overlay, (*AMBER, core_alpha), (int(self.lx), int(self.ly)), int(10 * (1 - st) + 4))

        surface.blit(overlay, (0, 0))


# ============================================================================
# HARVEST — field-wide bola detonation. The showpiece.
# ============================================================================

class HarvestAnimation:
    """He touches off every fused bola at once: amber detonation bursts and gunmetal
    shrapnel radiate from each bola'd enemy, with a heavy shake + flash."""

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.total_duration = 0.85
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback
        self.screen_flash = screen_flash_callback
        self.camera = camera

        # Find every enemy carrying bolas — those are the detonation points.
        self.blast_points: List[Tuple[float, float]] = []
        caster_gu = caster_unit.game_unit
        if game is not None:
            for u in getattr(game, 'units', []):
                if (u.is_alive() and u.player != caster_gu.player
                        and len(getattr(u, 'bolas', []) or []) > 0):
                    self.blast_points.append(_grid_center(camera, u.y, u.x))
        if not self.blast_points:
            # Fallback: detonate at the caster so something always shows.
            self.blast_points.append(_grid_center(camera, caster_gu.y, caster_gu.x))

        self.ignite_done = False
        self.detonate_done = False

    def update(self, delta_time):
        self.elapsed += delta_time

        # Ignite: a brief warm-up flicker at each point. (Harvest's primary sound is
        # played by the factory via SKILL_SOUNDS on creation.)
        if not self.ignite_done and self.elapsed > 0.02:
            self.ignite_done = True
            if self.particle_emitter:
                for (bx, by) in self.blast_points:
                    self.particle_emitter.emit_burst(bx, by, AMBER, count=4)

        # Detonate: the big multi-point pop.
        if not self.detonate_done and self.elapsed >= 0.22:
            self.detonate_done = True
            if self.particle_emitter:
                for (bx, by) in self.blast_points:
                    self.particle_emitter.emit_burst(bx, by, AMBER, count=16)
                    self.particle_emitter.emit_burst(bx, by, AMBER_BRIGHT, count=8)
                    self.particle_emitter.emit_burst(bx, by, BOMB_BLACK, count=10)
                    self.particle_emitter.emit_burst(bx, by, GUNMETAL_LIGHT, count=6)
                    self.particle_emitter.emit_burst(bx, by, SMOKE, count=6)
            if self.screen_shake:
                self.screen_shake(9, 0.3)
            if self.screen_flash:
                self.screen_flash(AMBER, 0.12)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        for (bx, by) in self.blast_points:
            # Ignite glow before the pop.
            if not self.detonate_done and self.elapsed > 0.02:
                it = min(1.0, self.elapsed / 0.22)
                glow_alpha = int(120 * it)
                pygame.draw.circle(overlay, (*AMBER, glow_alpha), (int(bx), int(by)), int(6 + it * 4))

            # Detonation: expanding shockwave + shrapnel streaks + hot core.
            if self.detonate_done:
                dt = min(1.0, (self.elapsed - 0.22) / (self.total_duration - 0.22))
                # shockwave rings
                ring_r = int(TILE_SIZE * 0.3 + dt * TILE_SIZE * 1.7)
                ring_alpha = max(0, int(210 * (1 - dt)))
                if ring_alpha > 0:
                    pygame.draw.circle(overlay, (*AMBER_BRIGHT, ring_alpha), (int(bx), int(by)), ring_r, 3)
                    pygame.draw.circle(overlay, (*AMBER, max(0, ring_alpha - 70)),
                                       (int(bx), int(by)), int(ring_r * 0.65), 2)
                # radial shrapnel streaks
                streak_alpha = max(0, int(220 * (1 - dt)))
                if streak_alpha > 0:
                    for k in range(8):
                        a = math.radians(k * 45 + 10)
                        r0 = TILE_SIZE * 0.4 + dt * TILE_SIZE * 0.6
                        r1 = r0 + TILE_SIZE * 0.5
                        x0, y0 = bx + math.cos(a) * r0, by + math.sin(a) * r0
                        x1, y1 = bx + math.cos(a) * r1, by + math.sin(a) * r1
                        pygame.draw.line(overlay, (*GUNMETAL_LIGHT, streak_alpha),
                                         (int(x0), int(y0)), (int(x1), int(y1)), 2)
                # hot core
                core_alpha = max(0, int(230 * (1 - dt)))
                if core_alpha > 0:
                    pygame.draw.circle(overlay, (*AMBER, core_alpha), (int(bx), int(by)), int(12 * (1 - dt) + 3))
                    pygame.draw.circle(overlay, (255, 255, 255, max(0, int(200 * (1 - dt)))),
                                       (int(bx), int(by)), int(6 * (1 - dt) + 1))

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
