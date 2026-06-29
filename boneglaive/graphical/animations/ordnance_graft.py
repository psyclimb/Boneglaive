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
from boneglaive.graphical.animations.core import (
    TILE_SIZE, Particle
)

from boneglaive.graphical.sound_helper import play_sound

# ============================================================================
# ORDNANCE GRAFT COLOR PALETTE
# ============================================================================

OLIVE = (75, 83, 32)
OLIVE_DARK = (47, 54, 20)
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


def _draw_bomb_cluster(overlay, cx, cy, scale, alpha, rot=0.0):
    """Draw the staff's grape-cluster of spiked bombs (matches the SVG's detonator head):
    a tight bunch of small spiked balls with one amber trigger-glint. Used on the linstock
    tip so the weapon reads as the bomb-tipped detonator staff, not a plain pole."""
    # bunch of 3 small spiked balls clustered like grapes
    for ox, oy, r in ((0.0, -1.4, 1.9), (-1.5, 0.9, 1.7), (1.5, 0.9, 1.7)):
        _draw_spiked_bomb(overlay, cx + ox * scale, cy + oy * scale,
                          r * scale, alpha, rot + ox * 20)
    # amber radio-trigger glint nestled in the cluster (the firing button accent)
    pygame.draw.circle(overlay, (*AMBER, alpha), (int(cx), int(cy)), max(1, int(0.9 * scale)))


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
# Shared INOCULATION sequence: the weird centerpiece. A delivered bomb SEATS proud
# of the body, then BURROWS (twists + sinks "under the skin" while a wound ring
# closes over it and a couple of specks are ejected), then ARMS (amber pulse rings
# + a live pinprick ember). Surgical/clean body-horror. Both Inoculant variants
# drive one of these so the graft step is byte-identical between graft and drone.
# ============================================================================

class _Inoculation:
    """The bomb settling INTO the target and arming. Pure visual sub-animation; the
    owning animation calls update(dt)/draw(surface) and passes the strike direction so
    the bomb sinks 'inward' along the line of delivery."""

    SEAT = 0.12          # bomb sits proud, contact shudder
    BURROW = 0.45        # twists + sinks under the skin; wound ring closes (eased slow so it reads)
    ARM = 0.32           # amber pulse rings; it wakes up
    TOTAL = SEAT + BURROW + ARM
    SIZE = 1.6           # overall size multiplier for all seat/burrow/arm visuals

    def __init__(self, tx, ty, ux, uy, emitter, screen_shake,
                 start_size=5.5, seated_size=2.4, base_rot=0.0,
                 spin_carry=0.0, scale=1.0, start_delay=0.0, play_audio=True):
        # tx,ty = entry point; ux,uy = unit vector pointing INTO the body (delivery dir).
        # start_delay holds the element idle (drawing nothing) until that much time has
        # passed, so a single owner can stagger several graft-ins (Skyhook on N enemies,
        # Booster Charge's 2nd bomb, Chain Reaction's seed) off one clock.
        # play_audio gates the burrow/arm SOUND so it fires once PER CAST, not per bomb:
        # a multi-bomb skill (Skyhook/Harvest-chain/Booster) would otherwise machine-gun N
        # overlapping copies into mud (and exhaust mixer channels). Grouped/extra bombs are
        # visual-only for sound; the owning animation's slam/detonation carries the audio.
        self.tx, self.ty = tx, ty
        self.ux, self.uy = ux, uy
        self.emitter = emitter
        self.screen_shake = screen_shake or (lambda i, d: None)
        self.start_size = start_size * self.SIZE
        self.seated_size = seated_size * self.SIZE
        self.base_rot = base_rot
        self.spin_carry = spin_carry      # extra deg the drone round was already spinning
        self.scale = scale
        self.start_delay = start_delay
        self.play_audio = play_audio
        self.elapsed = -start_delay       # counts up; own beats begin once it reaches 0
        self._shuddered = False
        self._burrowed = False
        self._armed = False
        self._pulses = []                 # (fire_time,) list for staggered arm rings
        for k in range(3):
            self._pulses.append(0.001 + self.SEAT + self.BURROW + k * 0.10)

    @property
    def active(self):
        return self.elapsed < self.TOTAL

    def _eject_specks(self, n, speed_lo, speed_hi):
        """A few dark body specks flung outward from the entry (the body pushing back)."""
        if not self.emitter:
            return
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(speed_lo, speed_hi)
            p = Particle(self.tx, self.ty, math.cos(a) * sp, math.sin(a) * sp,
                         random.choice((BOMB_BLACK, BOMB_EDGE, OLIVE_DARK)),
                         random.uniform(1.2, 2.2) * self.scale * self.SIZE, random.uniform(0.18, 0.34))
            p.gravity = 140
            self.emitter.particles.append(p)

    def update(self, delta_time):
        self.elapsed += delta_time

        # SEAT beat: a small contact shudder the instant it lands proud.
        if not self._shuddered and self.elapsed >= 0.0:
            self._shuddered = True
            self.screen_shake(3, 0.09)

        # BURROW beat: it bites in — suction pull inward + a couple specks ejected.
        if not self._burrowed and self.elapsed >= self.SEAT:
            self._burrowed = True
            if self.play_audio:
                play_sound("inoculant_burrow")
            _emit_graft_inward(self.emitter, self.tx, self.ty,
                               n=int(8 * self.scale) + 5, color=BOMB_BLACK)
            self._eject_specks(3, 45, 90)

        # ARM beat: it wakes up under the skin — one short sound.
        if not self._armed and self.elapsed >= self.SEAT + self.BURROW:
            self._armed = True
            if self.play_audio:
                play_sound("inoculant_arm")

        return self.active

    def _burrow_t(self):
        """0 during seat, 0->1 across the burrow, 1 after (clamped)."""
        return max(0.0, min(1.0, (self.elapsed - self.SEAT) / self.BURROW))

    def draw(self, overlay):
        if not self.active or self.elapsed < 0.0:       # idle during the start delay
            return
        bt = self._burrow_t()
        ease = bt * bt                                  # accelerate inward (auger bite)

        # sub-dermal amber glow blooms UNDER the entry as it takes hold (drawn first so
        # the bomb sinks over it). Peaks at the end of the burrow, lingers through arm.
        glow_t = max(0.0, min(1.0, (self.elapsed - self.SEAT) / (self.BURROW + self.ARM)))
        ga = int(70 * math.sin(min(1.0, glow_t) * math.pi))
        if ga > 0:
            pygame.draw.circle(overlay, (*AMBER_DARK, ga),
                               (int(self.tx), int(self.ty)), int((4 + glow_t * 4) * self.scale * self.SIZE))

        # the bomb itself: shrinks as it sinks, nudged a few px into the body, and
        # SCREWS in (rotation threads the spikes inward instead of just shrinking).
        size = (self.start_size + (self.seated_size - self.start_size) * ease)
        sink = ease * 3.0 * self.scale * self.SIZE      # px driven under the surface
        bx = self.tx + self.ux * sink
        by = self.ty + self.uy * sink
        twist = self.base_rot + self.spin_carry * (1 - ease) + ease * 150  # auger + carry
        if size > 0.4:
            # contact shadow ring under the bomb while it's still proud (seat->early burrow)
            if bt < 0.6:
                sa = int(90 * (1 - bt / 0.6))
                pygame.draw.circle(overlay, (*BOMB_BLACK, sa),
                                   (int(self.tx), int(self.ty)), int(size * 1.25), 1)
            _draw_spiked_bomb(overlay, bx, by, size, 255, twist)

        # puckering WOUND RING that contracts over the entry as the bomb sinks under.
        if bt > 0.02:
            wound_r = int(size * 1.5 * self.scale + (1 - ease) * 5 * self.scale * self.SIZE)
            wa = int(150 * (1 - bt * 0.7))
            if wa > 0 and wound_r > 0:
                pygame.draw.circle(overlay, (*OLIVE_DARK, wa),
                                   (int(self.tx), int(self.ty)), wound_r, 1)

        # ARM beat: amber pulse rings expand + fade from the entry (it's live now), with
        # a live pinprick ember glinting each pulse (ties to his amber radio trigger).
        for pt in self._pulses:
            dt = self.elapsed - pt
            if dt < 0:
                continue
            rt = dt / 0.24
            if rt > 1.0:
                continue
            ring_r = int((2 + rt * 9) * self.scale * self.SIZE)
            ring_a = int(180 * (1 - rt))
            if ring_a > 0:
                pygame.draw.circle(overlay, (*AMBER, ring_a),
                                   (int(self.tx), int(self.ty)), ring_r, 2)
            # pinprick ember at the entry as each pulse fires
            ea = int(220 * (1 - rt))
            if ea > 0:
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, ea),
                                   (int(self.tx), int(self.ty)), max(1, int(1.6 * self.scale * self.SIZE)))


def _make_inoculations(tiles, camera, emitter, screen_shake, base_delay=0.0,
                       stagger=0.08, scale=1.0):
    """Build a staggered list of _Inoculation graft-ins, one per (grid_y, grid_x) tile.

    Used by skills that plant on several enemies at once (Skyhook) or one chained body
    (Chain Reaction) so every bomb the graft applies burrows in with the same seat/arm
    sequence as Inoculant. Each sinks toward its OWN tile center (no incoming strike
    vector at these sites, so the bombs auger straight down). Returns the list; the
    owning animation ticks/draws them and sizes its duration to outlast them."""
    inocs = []
    for i, (gy, gx) in enumerate(tiles):
        ex, ey = _grid_center(camera, gy, gx)
        inocs.append(_Inoculation(
            ex, ey, 0.0, 1.0,                 # sink "down" (+y) into the tile
            emitter, screen_shake,
            base_rot=random.uniform(0, 60),
            scale=scale,
            start_delay=base_delay + i * stagger,
            play_audio=False,                 # owner's slam/detonation carries the sound
        ))
    return inocs


# ============================================================================
# INOCULANT (GRAFT) — he sweeps the linstock into the enemy; bombs graft in.
# ============================================================================

class InoculantAnimation:
    """The graft's Inoculant: the bomb-tipped detonator staff winds back, sweeps into the
    target with a motion-blur swipe, and transfers ONE spiked bomb off its grape-cluster
    head onto the enemy. The bomb then SEATS, BURROWS under the skin (twisting in as a
    wound ring closes over it), and ARMS (amber pulses) — the weird inoculation. Body
    stays put; the weapon does the work."""

    WINDUP = 0.12
    STRIKE = 0.24   # weapon connects here
    TOTAL = STRIKE + _Inoculation.TOTAL + 0.05   # strike + the full graft-in sequence

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
        # The swing ADAPTS to range: the staff extends along the aim line exactly far
        # enough to reach the target at full strike (Inoculant is range 2, so the target
        # can sit ~1 to ~2.8 tiles away on screen). A short reach (~1 tile) reads as a
        # swat with a wide wrist-arc; a long reach reads as a committed thrust/lunge — so
        # as distance grows we extend the reach and FLATTEN the perpendicular arc into a
        # straighter jab. Tip lands on (tx,ty) regardless, so the bomb transfers cleanly.
        self.aim_reach = dist                                    # along-aim travel = true gap
        tiles = dist / max(1.0, TILE_SIZE)
        self.thrust_bias = max(0.0, min(1.0, tiles - 1.0))       # 0 @ <=1 tile -> 1 @ >=2 tiles
        self.bomb_rot = random.uniform(0, 60)
        self.connected = False
        self.swing_sound_played = False
        self.inoc = None                                          # the seat/burrow/arm sub-anim
        self.extra_inocs = []                                     # Booster Charge's extra bombs
        # How many bombs actually seated this strike (Booster Charge seats 2). Read from the
        # data the skill recorded; default 1 if absent (e.g. older state / the drone).
        caster_gu = getattr(caster_unit, 'game_unit', None)
        data = getattr(caster_gu, 'last_inoculant_data', None) if caster_gu else None
        self.planted = max(1, data.get('planted', 1)) if data else 1
        # A 2nd planted bomb extends the animation so its staggered graft-in finishes too.
        if self.planted >= 2:
            self.TOTAL = self.STRIKE + 0.14 + _Inoculation.TOTAL + 0.05

    def update(self, delta_time):
        self.elapsed += delta_time

        # Swing beat — the linstock winds back and sweeps in (start of the strike).
        if not self.swing_sound_played:
            self.swing_sound_played = True
            play_sound("inoculant_swing")

        # Connection beat — spark + shake, and kick off the inoculation (bomb grafts in).
        if not self.connected and self.elapsed >= self.STRIKE:
            self.connected = True
            play_sound("inoculant_strike")
            if self.particle_emitter:
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER, count=12)
                self.particle_emitter.emit_burst(self.tx, self.ty, AMBER_BRIGHT, count=6)
                self.particle_emitter.emit_burst(self.tx, self.ty, GUNMETAL_LIGHT, count=5)
            if self.screen_shake:
                self.screen_shake(4, 0.14)
            self.inoc = _Inoculation(self.tx, self.ty, self.ux, self.uy,
                                     self.particle_emitter, self.screen_shake,
                                     start_size=5.5, seated_size=2.4, base_rot=self.bomb_rot)
            # Booster Charge: a 2nd (and rarely more) bomb seats right after the first,
            # staggered so the player reads two distinct graft-ins, not one fat blob. The
            # extras are visual-only for sound — the one burrow/arm from self.inoc covers
            # the strike (they all seat from the same blow; N squelches would muddy it).
            for k in range(1, self.planted):
                self.extra_inocs.append(_Inoculation(
                    self.tx, self.ty, self.ux, self.uy,
                    self.particle_emitter, self.screen_shake,
                    start_size=5.0, seated_size=2.2,
                    base_rot=random.uniform(0, 60), start_delay=0.14 * k,
                    play_audio=False))

        if self.inoc is not None:
            self.inoc.update(delta_time)
        for e in self.extra_inocs:
            e.update(delta_time)

        if self.elapsed >= self.TOTAL:
            self.active = False
        return self.active

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # ---- the linstock: winds back, then sweeps/thrusts out to reach the target ----
        # The perpendicular wrist-arc stays a fixed visual width (it's a cock of the wrist,
        # not a reach) and flattens as the strike becomes a long thrust; only the along-aim
        # extension grows with distance, ending exactly on the target.
        swing_w = TILE_SIZE * 0.6 * (1.0 - 0.7 * self.thrust_bias)   # fixed-ish arc width
        if self.elapsed < self.STRIKE + 0.06:
            if self.elapsed < self.WINDUP:
                # windup: tip pulled back behind the graft, off the swing plane
                wt = self.elapsed / self.WINDUP
                tipx = self.cx - self.ux * (TILE_SIZE * 0.15) + self.px * swing_w * (0.6 + 0.4 * wt)
                tipy = self.cy - self.uy * (TILE_SIZE * 0.15) + self.py * swing_w * (0.6 + 0.4 * wt)
            else:
                # strike: tip races out along the aim line all the way to the target,
                # swinging in from the windup side (the sideways arc decays to 0 on contact)
                st = min(1.0, (self.elapsed - self.WINDUP) / (self.STRIKE - self.WINDUP))
                ease = 1 - (1 - st) * (1 - st)
                swing = (1 - ease)
                tipx = self.cx + self.ux * self.aim_reach * ease + self.px * swing_w * swing
                tipy = self.cy + self.uy * self.aim_reach * ease + self.py * swing_w * swing
            buttx = self.cx - self.ux * (TILE_SIZE * 0.22)
            butty = self.cy - self.uy * (TILE_SIZE * 0.22)
            a = 235
            # motion-blur swipe arc during the strike — spans from near the caster out to
            # the tip, so it stretches into a streak on a long thrust and stays an arc on a
            # short swat (perpendicular kick scales with the same arc width).
            if self.elapsed >= self.WINDUP:
                st = min(1.0, (self.elapsed - self.WINDUP) / (self.STRIKE - self.WINDUP))
                blur_a = int(120 * (1 - abs(st - 0.7)))
                if blur_a > 0:
                    kick = swing_w * 0.22
                    pygame.draw.line(overlay, (*AMBER_BRIGHT, blur_a),
                                     (int(self.cx + self.ux * TILE_SIZE * 0.4 + self.px * kick),
                                      int(self.cy + self.uy * TILE_SIZE * 0.4 + self.py * kick)),
                                     (int(tipx), int(tipy)), 4)
            # tan shaft + grain
            pygame.draw.line(overlay, (*TAN, a), (int(buttx), int(butty)), (int(tipx), int(tipy)), 4)
            pygame.draw.line(overlay, (*OLIVE_DARK, max(0, a - 60)), (int(buttx), int(butty)), (int(tipx), int(tipy)), 1)
            # gunmetal collar at the head, then the grape-cluster of bombs (the detonator
            # head from his SVG) — until the strike lands, after which the cluster is
            # "one bomb lighter" and the transferred bomb lives on the target.
            pygame.draw.circle(overlay, (*GUNMETAL, a), (int(tipx), int(tipy)), 3)
            pygame.draw.circle(overlay, (*GUNMETAL_LIGHT, a), (int(tipx), int(tipy)), 3, 1)
            cluster_scale = 1.0 if not self.connected else 0.8
            _draw_bomb_cluster(overlay, tipx, tipy - 3, cluster_scale, a, self.bomb_rot)

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

        # ---- the bomb seats, burrows under the skin, and arms (the weird part) ----
        if self.inoc is not None:
            self.inoc.draw(overlay)
        for e in self.extra_inocs:                       # Booster Charge's extra bomb(s)
            e.draw(overlay)

        surface.blit(overlay, (0, 0))


# ============================================================================
# INOCULANT (DRONE) — it fires a spiked-bomb projectile that grafts into the target.
# ============================================================================

class DroneInoculantAnimation:
    """The drone's Inoculant: a muzzle flash + rotor blur at the drone, a spiked-bomb
    projectile spins across to the target trailing amber — then DRILLS in. The round's
    flight-spin carries straight through into the burrow, so it reads as a self-tunnelling
    inoculant dart: spinning in the air, then spinning IN under the skin, where it seats,
    a wound closes over it, and it arms (amber pulses)."""

    FIRE = 0.04
    HIT = 0.26       # projectile reaches the target
    SPIN_AT_HIT = 360.0 * (HIT - FIRE) / 0.25   # deg the round has spun on arrival (carry)
    TOTAL = HIT + _Inoculation.TOTAL + 0.05

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
        # flight direction = the line the round drills in along (into the body)
        dx, dy = self.tx - self.sx, self.ty - self.sy
        dist = max(1.0, math.hypot(dx, dy))
        self.ux, self.uy = dx / dist, dy / dist
        self.bomb_rot = random.uniform(0, 60)
        self.fired = False
        self.hit = False
        self.inoc = None

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
            if self.screen_shake:
                self.screen_shake(3, 0.12)
            # hand the round off to the inoculation: a lighter round (smaller scale), and
            # its flight-spin carries into the auger twist so the drill read is continuous.
            # play_audio=False: the drone has its OWN single graft sound (drone_inoculant_graft,
            # fired just above, covering embed+settle); it does NOT borrow the graft's
            # melee-flavored burrow/arm sounds — keeps the drone at its 2 spec'd sound files.
            self.inoc = _Inoculation(self.tx, self.ty, self.ux, self.uy,
                                     self.particle_emitter, self.screen_shake,
                                     start_size=4.6, seated_size=2.0,
                                     base_rot=self.bomb_rot + self.SPIN_AT_HIT,
                                     play_audio=False,
                                     spin_carry=140.0, scale=0.85)

        if self.inoc is not None:
            self.inoc.update(delta_time)

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
            # the tumbling spiked bomb (spin rate matches SPIN_AT_HIT so the carry is seamless)
            _draw_spiked_bomb(overlay, bx, by, 4.0, 255, self.bomb_rot + t * self.SPIN_AT_HIT)

        # ---- impact spark on the target ----
        if self.hit:
            it = min(1.0, (self.elapsed - self.HIT) / 0.18)
            fa = max(0, int(190 * (1 - it)))
            if fa > 0:
                pygame.draw.circle(overlay, (*AMBER, fa), (int(self.tx), int(self.ty)), int(6 + it * 8))
                pygame.draw.circle(overlay, (*AMBER_BRIGHT, fa), (int(self.tx), int(self.ty)), int(3 + it * 4))

        # ---- the round drills in, seats, and arms (the weird part) ----
        if self.inoc is not None:
            self.inoc.draw(overlay)

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
        self._landed_at_total = False

        # Graft-ins for every bomb the slam plants (read from the data execute() recorded).
        # Each starts just as he touches down, staggered so a multi-enemy slam reads as a
        # quick succession of bombs biting home rather than one mush. The controller stays
        # alive past its normal end until these finish; landing/drone-reveal still happen
        # on time (at TOTAL) so the sprite doesn't hang in the air.
        self._slam_at = self.CARRY_END * self.TOTAL + (self.TOTAL - self.CARRY_END * self.TOTAL) * 0.85
        plants = []
        sky_data = getattr(graft_gu, 'last_skyhook_data', None) if graft_gu else None
        if sky_data and sky_data.get('plants'):
            plants = list(sky_data['plants'])
            graft_gu.last_skyhook_data = None  # consume so it doesn't replay next cast
        self.inocs = _make_inoculations(plants, self.camera, self.particle_emitter,
                                        self.screen_shake, base_delay=self._slam_at + 0.02,
                                        stagger=0.09)
        last_finish = (max((ino.start_delay for ino in self.inocs), default=0.0)
                       + _Inoculation.TOTAL) if self.inocs else 0.0
        self._anim_end = max(self.TOTAL, last_finish + 0.03)

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

        # Tick the per-bomb graft-ins (they idle until their start delay, around touchdown).
        for ino in self.inocs:
            ino.update(delta_time)

        # Land the sprite + reveal the drone ON TIME (at TOTAL) even though the controller
        # may stay alive a little longer to finish the graft-in visuals.
        if not self._landed_at_total and self.elapsed >= self.TOTAL:
            self._landed_at_total = True
            self._land_caster()
            self._reveal_drone()  # defensive: ensure the drone is never left hidden

        if self.elapsed >= self._anim_end:
            self._land_caster()
            self._reveal_drone()
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

        # Per-bomb graft-ins on the struck enemies (seat/burrow/arm), after the slam.
        for ino in self.inocs:
            ino.draw(overlay)

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

        # Chain Reaction upgrade: each chained victim gets a fresh bomb slammed in and
        # immediately blown. Show the graft-in (seat/burrow/arm) on those tiles, its SEAT
        # landing right as the detonation barrage fires so it reads as "a bomb rams home
        # and goes off." Empty list when the upgrade is off / nothing chained.
        chain_plants = harvest_data.get('chain_plants', []) if harvest_data else []
        self.inocs = _make_inoculations(chain_plants, camera, self.particle_emitter,
                                        self.screen_shake, base_delay=self.IGNITE_AT,
                                        stagger=0.06)

        # Total duration = the last blast's fire time + its lifetime, but never shorter
        # than the last chain graft-in needs to finish.
        blast_end = max(b['t0'] for b in self.blasts) + self.BLAST_DUR
        inoc_end = (max((ino.start_delay for ino in self.inocs), default=0.0)
                    + _Inoculation.TOTAL) if self.inocs else 0.0
        self.total_duration = max(blast_end, inoc_end + 0.03)
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

        # Chain Reaction graft-ins (a fresh bomb ramming into each chained victim).
        for ino in self.inocs:
            ino.update(delta_time)

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

        # Chain Reaction graft-ins, drawn over the blast so the seeded bomb is still
        # visibly seating/arming as the fireball clears.
        for ino in self.inocs:
            ino.draw(overlay)

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
