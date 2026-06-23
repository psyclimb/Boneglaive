#!/usr/bin/env python3
"""
Graphical animations for the ORDNANCE GRAFT unit type and its QUADCOPTER drone summon.
Skill animations with particles, screen effects, and phased sequencing.

Color scheme matches the ORDNANCE GRAFT sprite: olive drab, gunmetal, black spiked
bombs, and an amber fuse/ember accent.
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
    """Return the polygon points of a spiked ball (his bomb motif) for pygame.draw."""
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
# Shared "graft-in" flair: particles converging INWARD onto the bomb, suggesting it
# is being driven into the target's body (used by both Inoculant variants).
# ============================================================================

def _emit_graft_inward(emitter, tx, ty, n=8, color=BOMB_BLACK):
    """Spawn particles that start on a ring and rush IN toward (tx,ty) — the bomb being
    grafted into the body."""
    if not emitter:
        return
    for _ in range(n):
        a = random.uniform(0, math.tau)
        dist = random.uniform(10, 18)
        px, py = tx + math.cos(a) * dist, ty + math.sin(a) * dist
        sp = random.uniform(60, 120)
        # velocity points back toward the center
        p = Particle(px, py, -math.cos(a) * sp, -math.sin(a) * sp,
                     color, random.uniform(1.5, 3.0), random.uniform(0.18, 0.32))
        emitter.particles.append(p)


def _draw_target_pos(camera, target_unit, target_pos, caster_unit):
    """Resolve the target's screen position from the available references."""
    if target_pos is not None:
        return _grid_center(camera, target_pos[0], target_pos[1])
    if target_unit is not None:
        gu = getattr(target_unit, 'game_unit', target_unit)
        return _grid_center(camera, gu.y, gu.x)
    return _grid_center(camera, caster_unit.game_unit.y, caster_unit.game_unit.x)


# ============================================================================
# INOCULANT (GRAFT) — he sweeps the linstock into the enemy; bombs graft in.
# ============================================================================

class InoculantAnimation:
    """The graft's Inoculant: the linstock winds back, sweeps into the target with a
    motion-blur swipe and amber ember, then a spiked bomb thunks in and grafts (inward
    particles), with an impact spark + slash mark. Body stays put; the weapon does the work."""

    WINDUP = 0.12
    STRIKE = 0.24   # weapon connects here
    TOTAL = 0.6

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback

        self.cx, self.cy = caster_unit.x, caster_unit.y          # graft screen pos
        self.tx, self.ty = _draw_target_pos(camera, target_unit, target_pos, caster_unit)
        # aim direction graft -> target
        dx, dy = self.tx - self.cx, self.ty - self.cy
        dist = max(1.0, math.hypot(dx, dy))
        self.ux, self.uy = dx / dist, dy / dist
        self.px, self.py = -self.uy, self.ux                      # perpendicular (swing plane)
        self.bomb_rot = random.uniform(0, 60)
        self.connected = False
        self.swing_sound_played = False

    def update(self, delta_time):
        self.elapsed += delta_time

        # Swing beat — the linstock winds back and sweeps in (start of the strike).
        if not self.swing_sound_played:
            self.swing_sound_played = True
            play_sound("inoculant_swing")

        # Connection beat — spark + graft + shake when the linstock lands.
        if not self.connected and self.elapsed >= self.STRIKE:
            self.connected = True
            play_sound("inoculant_strike")
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=12)
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER_BRIGHT, count=6)
                self.particle_emitter.emit_burst(self.tx, self.ty, GUNMETAL_LIGHT, count=5)
                _emit_graft_inward(self.particle_emitter, self.tx, self.ty, n=9)
            if self.screen_shake:
                self.screen_shake(4, 0.14)

        if self.elapsed >= self.TOTAL:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # ---- the linstock: winds back, then sweeps into the target ----
        if self.elapsed < self.STRIKE + 0.06:
            if self.elapsed < self.WINDUP:
                # windup: tip pulled back behind the graft, off the swing plane
                wt = self.elapsed / self.WINDUP
                reach = TILE_SIZE * 0.5
                tipx = self.cx - self.ux * reach * 0.3 + self.px * reach * (0.6 + 0.4 * wt)
                tipy = self.cy - self.uy * reach * 0.3 + self.py * reach * (0.6 + 0.4 * wt)
            else:
                # strike: tip races along an arc from the windup side to the target
                st = min(1.0, (self.elapsed - self.WINDUP) / (self.STRIKE - self.WINDUP))
                ease = 1 - (1 - st) * (1 - st)
                reach = TILE_SIZE * 0.95
                # blend from perpendicular windup to the aim line
                swing = (1 - ease)
                tipx = self.cx + self.ux * reach * ease + self.px * reach * 0.7 * swing
                tipy = self.cy + self.uy * reach * ease + self.py * reach * 0.7 * swing
            buttx = self.cx - self.ux * (TILE_SIZE * 0.22)
            butty = self.cy - self.uy * (TILE_SIZE * 0.22)
            a = 235
            # motion-blur swipe arc during the strike
            if self.elapsed >= self.WINDUP:
                st = min(1.0, (self.elapsed - self.WINDUP) / (self.STRIKE - self.WINDUP))
                blur_a = int(120 * (1 - abs(st - 0.7)))
                if blur_a > 0:
                    pygame.draw.line(overlay, (*AMBER_BRIGHT, blur_a),
                                     (int(self.cx + self.ux * TILE_SIZE * 0.4 + self.px * 8),
                                      int(self.cy + self.uy * TILE_SIZE * 0.4 + self.py * 8)),
                                     (int(tipx), int(tipy)), 4)
            # tan shaft + grain
            pygame.draw.line(overlay, (*TAN, a), (int(buttx), int(butty)), (int(tipx), int(tipy)), 4)
            pygame.draw.line(overlay, (*OLIVE_DARK, max(0, a - 60)), (int(buttx), int(butty)), (int(tipx), int(tipy)), 1)
            # gunmetal head + amber slow-match ember at the tip
            pygame.draw.circle(overlay, (*GUNMETAL, a), (int(tipx), int(tipy)), 4)
            pygame.draw.circle(overlay, (*GUNMETAL_LIGHT, a), (int(tipx), int(tipy)), 4, 1)
            ember_r = 2 + int(abs(math.sin(self.elapsed * 30)))
            pygame.draw.circle(overlay, (*AMBER, a), (int(tipx + self.px * 4), int(tipy + self.py * 4)), ember_r)

        # ---- impact: spark flash + a short slash mark across the target ----
        if self.connected:
            it = min(1.0, (self.elapsed - self.STRIKE) / 0.18)
            fa = max(0, int(190 * (1 - it)))
            if fa > 0:
                pygame.draw.circle(overlay, (*AMBER, fa), (int(self.tx), int(self.ty)), int(7 + it * 9))
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, fa), (int(self.tx), int(self.ty)), int(3 + it * 4))
                # slash mark along the swing direction
                sl = TILE_SIZE * 0.5
                pygame.draw.line(overlay, (*AMBER_BRIGHT, fa),
                                 (int(self.tx - self.px * sl - self.ux * sl * 0.3),
                                  int(self.ty - self.py * sl - self.uy * sl * 0.3)),
                                 (int(self.tx + self.px * sl + self.ux * sl * 0.3),
                                  int(self.ty + self.py * sl + self.uy * sl * 0.3)), 2)

        # ---- the planted bomb thunks in and settles ----
        if self.elapsed > self.STRIKE:
            bt = min(1.0, (self.elapsed - self.STRIKE) / 0.28)
            ease = 1 - (1 - bt) * (1 - bt)
            size = 5.5 * ease
            jiggle = math.sin(self.elapsed * 45) * (1 - bt) * 2
            bomb_alpha = int(255 * min(1.0, (self.elapsed - self.STRIKE) / 0.18))
            if size > 0.5:
                _draw_spiked_bomb(overlay, self.tx + jiggle, self.ty, size, bomb_alpha, self.bomb_rot)

        surface.blit(overlay, (0, 0))


# ============================================================================
# INOCULANT (DRONE) — it fires a spiked-bomb projectile that grafts into the target.
# ============================================================================

class DroneInoculantAnimation:
    """The drone's Inoculant: a muzzle flash + rotor blur at the drone, a spiked-bomb
    projectile spins across to the target trailing amber, then grafts in (inward particles)
    with an impact spark. Reads as the drone shooting a bomb that embeds in the enemy."""

    FIRE = 0.04
    HIT = 0.26       # projectile reaches the target
    TOTAL = 0.6

    def __init__(self, caster_unit, target_unit=None, target_pos=None,
                 is_crit=False, is_infused=False,
                 particle_emitter=None, debris_list=None,
                 screen_shake_callback=None, screen_flash_callback=None,
                 units_list=None, camera=None, game=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback

        self.sx, self.sy = caster_unit.x, caster_unit.y          # drone screen pos
        self.tx, self.ty = _draw_target_pos(camera, target_unit, target_pos, caster_unit)
        self.bomb_rot = random.uniform(0, 60)
        self.fired = False
        self.hit = False

    def update(self, delta_time):
        self.elapsed += delta_time

        if not self.fired and self.elapsed >= self.FIRE:
            self.fired = True
            play_sound("drone_inoculant_fire")
            # muzzle flash / rotor wash at the drone
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.sx, self.sy, AMBER, count=6)
                self.particle_emitter.emit_trail(self.sx, self.sy, GUNMETAL_LIGHT, count=3)

        if not self.hit and self.elapsed >= self.HIT:
            self.hit = True
            play_sound("drone_inoculant_graft")
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=12)
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER_BRIGHT, count=6)
                _emit_graft_inward(self.particle_emitter, self.tx, self.ty, n=9)
            if self.screen_shake:
                self.screen_shake(3, 0.12)

        if self.elapsed >= self.TOTAL:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # ---- muzzle flash + rotor blur at the drone on fire ----
        if self.fired and self.elapsed < self.FIRE + 0.14:
            mt = (self.elapsed - self.FIRE) / 0.14
            ma = max(0, int(200 * (1 - mt)))
            if ma > 0:
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, ma), (int(self.sx), int(self.sy)), int(4 + mt * 4))
                pygame.draw.ellipse(overlay, (*GUNMETAL_LIGHT, ma),
                                    (int(self.sx - 9), int(self.sy - 3), 18, 6), 1)

        # ---- the spiked-bomb projectile spins from drone to target ----
        if self.fired and not self.hit:
            t = (self.elapsed - self.FIRE) / (self.HIT - self.FIRE)
            t = max(0.0, min(1.0, t))
            bx = self.sx + (self.tx - self.sx) * t
            by = self.sy + (self.ty - self.sy) * t
            # amber tracer trailing behind the projectile
            trail_t = max(0.0, t - 0.18)
            trx = self.sx + (self.tx - self.sx) * trail_t
            try_ = self.sy + (self.ty - self.sy) * trail_t
            pygame.draw.line(overlay, (*AMBER, 150), (int(trx), int(try_)), (int(bx), int(by)), 2)
            pygame.draw.line(overlay, (*AMBER_BRIGHT, 200), (int(trx), int(try_)), (int(bx), int(by)), 1)
            # the tumbling spiked bomb
            _draw_spiked_bomb(overlay, bx, by, 4.0, 255, self.bomb_rot + t * 360)

        # ---- impact spark on the target ----
        if self.hit:
            it = min(1.0, (self.elapsed - self.HIT) / 0.18)
            fa = max(0, int(190 * (1 - it)))
            if fa > 0:
                pygame.draw.circle(overlay, (*AMBER, fa), (int(self.tx), int(self.ty)), int(6 + it * 8))
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, fa), (int(self.tx), int(self.ty)), int(3 + it * 4))

        # ---- the planted bomb settles in ----
        if self.hit:
            bt = min(1.0, (self.elapsed - self.HIT) / 0.26)
            ease = 1 - (1 - bt) * (1 - bt)
            size = 5.0 * ease
            bomb_alpha = int(255 * min(1.0, (self.elapsed - self.HIT) / 0.15))
            if size > 0.5:
                _draw_spiked_bomb(overlay, self.tx, self.ty, size, bomb_alpha, self.bomb_rot)

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

    def __init__(self, caster_unit, target_pos, particle_emitter, screen_shake_callback,
                 camera=None, units_list=None):
        self.caster = caster_unit
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback or (lambda i, d: None)
        self.camera = camera
        self.active = True
        self.elapsed = 0.0

        # Hide the REAL drone sprite for the duration — the drone is carrying him
        # (represented by the silhouette on the cable in this animation's overlay). It
        # reappears at its new leashed position when he lands. Same `teleport_hidden`
        # flag the renderer's draw loop honors (see Derelictionist defection anim).
        self.drone_animated = None
        graft_gu = getattr(caster_unit, 'game_unit', None)
        drone_gu = getattr(graft_gu, 'drone', None) if graft_gu else None
        if drone_gu is not None and units_list:
            for au in units_list:
                if getattr(au, 'game_unit', None) is drone_gu:
                    self.drone_animated = au
                    break
        if self.drone_animated is not None:
            self.drone_animated.teleport_hidden = True

        # Origin = where the sprite currently is (the visual hasn't moved yet).
        self.ox, self.oy = caster_unit.x, caster_unit.y
        # Destination screen pos. Use the caster's ACTUAL landed grid cell (execute() has
        # already moved the game unit and the teleport branch synced grid_x/grid_y) so the
        # sprite always ends exactly on its tile. Fall back to target_pos if grid isn't set.
        # IMPORTANT: compute SHAKE-FREE (raw GRID_OFFSET + grid*TILE), NOT camera.grid_to_screen
        # — that bakes in the live screen-shake offset, which would freeze the sprite off its
        # tile if a shake was active when the cast fired (the intermittent desync bug).
        tgy, tgx = target_pos
        dest_gx = getattr(caster_unit, 'grid_x', None)
        dest_gy = getattr(caster_unit, 'grid_y', None)
        if dest_gx is None or dest_gy is None:
            dest_gx, dest_gy = tgx, tgy
        from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
        self.dx = dest_gx * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
        self.dy = dest_gy * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y
        self.dest_grid = (dest_gx, dest_gy)

        self.arc_height = 150          # how high the lift carries him (he's hauled UP)
        self.slam_done = False
        self.launch_done = False

        # set up sprite-rotation state (the renderer reads wind_up_rotation)
        self.caster.wind_up_rotation = 0

        # Launch beat: cable snaps taut, dust kicks up at the origin.
        play_sound("skyhook_launch")
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
                self._land_caster()
                self._slam()

        if self.elapsed >= self.TOTAL:
            self._land_caster()
            self._reveal_drone()  # defensive: ensure the drone is never left hidden
            self.active = False
        return self.active

    def _land_caster(self):
        """Snap the graft sprite onto its tile and clear any movement state, so nothing
        (a residual walk-lerp, a stale target) can drag it off its actual grid cell."""
        self.caster.x, self.caster.y = self.dx, self.dy
        self.caster.target_x, self.caster.target_y = self.dx, self.dy
        self.caster.is_moving = False
        self.caster.wind_up_rotation = 0

    def _reveal_drone(self):
        """Un-hide the real drone sprite and snap it to its NEW grid position. The
        teleport branch synced its grid_x/grid_y but not its screen x/y (the anim is
        meant to handle that), so we place the sprite now — it reappears at the landing."""
        d = self.drone_animated
        if d is None:
            return
        # snap screen position to its current grid cell (it was relocated adjacent)
        from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
        nx = d.grid_x * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_X
        ny = d.grid_y * TILE_SIZE + TILE_SIZE // 2 + GRID_OFFSET_Y
        d.x, d.y = nx, ny
        d.target_x, d.target_y = nx, ny
        d.is_moving = False
        if getattr(d, 'teleport_hidden', False):
            d.teleport_hidden = False

    def _slam(self):
        # He's been dropped off — the real drone reappears at its new spot beside him.
        self._reveal_drone()
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
# HARVEST — field-wide bomb detonation. The showpiece.
# ============================================================================

class HarvestAnimation:
    """He touches off every fused bomb at once: amber detonation bursts and gunmetal
    shrapnel radiate from each bombed enemy, with a heavy shake + flash."""

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
        # last_harvest_data BEFORE the bombs are consumed — read them from there (the
        # live bombs lists are already cleared by the time this animation runs).
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
        self.ignite_sound_played = False

    def _erupt(self, b):
        """Spawn the heavy layered particle burst for one blast point."""
        bx, by = b['x'], b['y']
        # Each bomb's detonation crack (fires per blast — the chain reads as a barrage).
        play_sound("harvest_detonate")
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
        # Dark spiked-bomb fragments blown apart (bomb motif shattering).
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

        # Ignite beat — the fuses catch and the warm-up glow builds before the barrage.
        if not self.ignite_sound_played:
            self.ignite_sound_played = True
            play_sound("harvest_ignite")

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
    target, capped with an amber flick from the lit slow-match. Plants no bomb — his
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
        self.swing_sound_played = False

    def update(self, delta_time):
        self.elapsed += delta_time
        if not self.swing_sound_played:
            self.swing_sound_played = True
            play_sound("ordnance_attack_swing")
        if not self.impact_done and self.elapsed > 0.18:
            self.impact_done = True
            play_sound("ordnance_attack_impact")
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
# QUADCOPTER basic attack — a plain ranged shot (rotor buzz + amber tracer).
# It no longer plants a bomb; the drone grafts via its own Inoculant skill.
# ============================================================================

class OrdnanceDroneShotAttack:
    """The drone's basic attack: a rotor-buzz tracer fired at the target with an impact
    spark. A plain hit — no bomb. Uses AnimatedUnit screen positions (attacker.x/.y are px)."""

    def __init__(self, attacker_unit, target_unit=None,
                 particle_emitter=None, screen_shake_callback=None, **kwargs):
        self.active = True
        self.elapsed = 0.0
        self.total_duration = 0.4
        self.particle_emitter = particle_emitter
        self.screen_shake = screen_shake_callback or (lambda i, d: None)

        self.sx, self.sy = attacker_unit.x, attacker_unit.y
        if target_unit is not None:
            self.tx, self.ty = target_unit.x, target_unit.y
        else:
            self.tx, self.ty = self.sx, self.sy

        self.fired = False
        self.impact_done = False

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
            play_sound("ordnance_drone_impact")
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=8)
                self.particle_emitter.emit_burst(self.tx, self.ty, GUNMETAL_LIGHT, count=5)
            self.screen_shake(2, 0.1)

        if self.elapsed >= self.total_duration:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Amber tracer from drone to target (during flight), with a faint rotor blur.
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

        # Impact spark on the target (no bomb).
        if self.impact_done:
            it = min(1.0, (self.elapsed - 0.18) / 0.18)
            fa = max(0, int(190 * (1 - it)))
            if fa > 0:
                pygame.draw.circle(overlay, (*AMBER, fa), (int(self.tx), int(self.ty)), int(4 + it * 6))
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, fa), (int(self.tx), int(self.ty)), int(2 + it * 3))

        surface.blit(overlay, (0, 0))
