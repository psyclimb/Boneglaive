"""
trailer_spin.py - Unit billboard spin animation for Boneglaive trailer.

Each unit sprite appears to spin in 3D (like a card rotating on its vertical
axis). At the moment the card goes fully edge-on (zero width), it swaps to the
next unit. The result is one seamless continuous spin through all 10 units.

Controls:
  SPACE       - pause / unpause
  LEFT/RIGHT  - adjust spin speed
  UP/DOWN     - adjust sprite display scale
  R           - restart from first unit
  Q / Escape  - quit

Usage:
  python trailer_spin.py

  # To set a specific BPM so each full rotation lands on a beat:
  python trailer_spin.py --bpm 120

  # To set how many beats one full spin takes (default 2):
  python trailer_spin.py --bpm 120 --beats-per-spin 2

Record the window with OBS.
"""

import argparse
import io
import math
import os
import subprocess
import sys

import pygame

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WINDOW_W = 1280
WINDOW_H = 720

SPRITE_RENDER_SIZE = 256   # rsvg-convert target size (pre-scale)
DISPLAY_SCALE      = 3     # multiply rendered sprite for final display size

BG_COLOR     = (15, 15, 20)
SHADOW_COLOR = (0, 0, 0, 120)

# Earthbound-style background stripe colors — matched to Boneglaive main menu palette
# Dark apocalyptic purple/red tones, orange glow accents, bone highlights
BG_LAYER_A = [(26, 16, 22),  (50, 28, 35)]    # dark purple-red / muted rose (sky gradient tones)
BG_LAYER_B = [(80, 42, 28),  (40, 22, 18)]    # ember orange / deep charcoal (glow accent)

UNITS_DIR = os.path.join(os.path.dirname(__file__), "graphics", "units")

UNIT_ORDER = [
    "glaiveman",
    "potpourrist",
    "mandible_foreman",
    "derelictionist",
    "gas_machinist",
    "interferer",
    "grayman",
    "delphic_appraiser",
    "marrow_condenser",
    "fowl_contrivance",
]

DEFAULT_SPIN_DURATION = 1.472   # seconds for one full 360 spin — gives 7.36s for all 10 units
FPS                   = 60


# ---------------------------------------------------------------------------
# SVG loading via rsvg-convert
# ---------------------------------------------------------------------------

def load_svg_as_surface(svg_path: str, size: int) -> pygame.Surface:
    """Rasterize an SVG to a pygame Surface using rsvg-convert."""
    result = subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size),
         "-f", "png", svg_path],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"rsvg-convert failed for {svg_path}:\n{result.stderr.decode()}"
        )
    return pygame.image.load(io.BytesIO(result.stdout), "unit.png").convert_alpha()


# ---------------------------------------------------------------------------
# Spin math
# ---------------------------------------------------------------------------

def spin_x_scale(angle_rad: float) -> float:
    """
    Returns the horizontal scale factor [0..1] for a given rotation angle.
    Uses cosine so the scaling feels like true 3D perspective rotation.
    angle_rad=0 -> face-on (scale=1)
    angle_rad=pi/2 -> edge-on (scale=0)
    """
    return abs(math.cos(angle_rad))


def draw_earthbound_bg(surface: pygame.Surface, t: float) -> None:
    """
    Earthbound-style battle background: two layers of wavy horizontal stripes
    scrolling vertically in opposite directions.

    Rendered at 1/4 resolution then scaled up for performance.
    """
    w, h = surface.get_size()
    SW, SH = w // 4, h // 4   # small render resolution

    # Render layer A (base)
    small_a = pygame.Surface((SW, SH))
    col_a, col_b = BG_LAYER_A
    stripe_h, wave_freq, wave_amp, scroll_speed = 7, 2.5, 5.5, 10
    scroll = t * scroll_speed
    for py in range(SH):
        phase      = (py / SH) * wave_freq * math.pi * 2 + t * 1.8
        warp       = math.sin(phase) * wave_amp
        eff_y      = py + warp + scroll
        stripe_idx = int(eff_y / stripe_h) % 2
        color      = col_a if stripe_idx == 0 else col_b
        pygame.draw.line(small_a, color, (0, py), (SW - 1, py))

    # Render layer B (additive overlay — only its bright stripes show through)
    small_b = pygame.Surface((SW, SH), pygame.SRCALPHA)
    col_a, col_b = BG_LAYER_B
    stripe_h, wave_freq, wave_amp, scroll_speed = 5, 3.8, 3.5, -15
    scroll = t * scroll_speed
    for py in range(SH):
        phase      = (py / SH) * wave_freq * math.pi * 2 - t * 2.2
        warp       = math.sin(phase) * wave_amp
        eff_y      = py + warp + scroll
        stripe_idx = int(eff_y / stripe_h) % 2
        if stripe_idx == 0:
            # Only draw the bright stripe; leave dark stripe transparent
            r, g, b = col_a
            pygame.draw.line(small_b, (r, g, b, 140), (0, py), (SW - 1, py))

    small_a.blit(small_b, (0, 0))
    scaled = pygame.transform.scale(small_a, (w, h))
    surface.blit(scaled, (0, 0))


def is_right_half(angle_rad: float) -> bool:
    """True when we are in the 'opening' half of the spin (0->pi/2 or 3pi/2->2pi)."""
    a = angle_rad % (2 * math.pi)
    return a < math.pi / 2 or a >= 3 * math.pi / 2


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Boneglaive trailer spin animation")
    parser.add_argument("--bpm", type=float, default=None,
                        help="Song BPM — syncs spin duration to beats")
    parser.add_argument("--beats-per-spin", type=float, default=2.0,
                        help="How many beats one full spin takes (default: 2)")
    args = parser.parse_args()

    if args.bpm is not None:
        beat_duration     = 60.0 / args.bpm
        spin_duration     = beat_duration * args.beats_per_spin
    else:
        spin_duration     = DEFAULT_SPIN_DURATION

    print(f"Spin duration: {spin_duration:.3f}s per full rotation")
    if args.bpm:
        print(f"  ({args.bpm} BPM, {args.beats_per_spin} beats per spin)")

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Boneglaive - Unit Showcase Spin")
    clock = pygame.time.Clock()

    # Load all unit sprites
    print("Loading unit sprites...")
    sprites: list[pygame.Surface] = []
    names:   list[str]            = []
    for unit_name in UNIT_ORDER:
        svg_path = os.path.join(UNITS_DIR, f"{unit_name}.svg")
        if not os.path.exists(svg_path):
            print(f"  WARNING: {svg_path} not found, skipping")
            continue
        print(f"  {unit_name}")
        surf = load_svg_as_surface(svg_path, SPRITE_RENDER_SIZE)
        sprites.append(surf)
        names.append(unit_name)

    if not sprites:
        print("No sprites loaded. Check UNITS_DIR path.")
        sys.exit(1)

    n           = len(sprites)
    angle       = 0.0          # current rotation angle in radians
    prev_angle  = 0.0
    unit_index  = 0            # which sprite is currently showing
    paused      = False
    speed_mult  = 1.0
    disp_scale  = DISPLAY_SCALE
    bg_time     = 0.0          # elapsed time for background animation

    center_x = WINDOW_W // 2
    center_y = WINDOW_H // 2

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    speed_mult = min(speed_mult * 1.25, 8.0)
                    print(f"Speed: {speed_mult:.2f}x")
                elif event.key == pygame.K_LEFT:
                    speed_mult = max(speed_mult / 1.25, 0.1)
                    print(f"Speed: {speed_mult:.2f}x")
                elif event.key == pygame.K_UP:
                    disp_scale = min(disp_scale + 0.5, 8.0)
                elif event.key == pygame.K_DOWN:
                    disp_scale = max(disp_scale - 0.5, 0.5)
                elif event.key == pygame.K_r:
                    angle      = 0.0
                    prev_angle = 0.0
                    unit_index = 0

        if not paused:
            bg_time    += dt
            prev_angle  = angle
            angle_delta = (2 * math.pi / spin_duration) * dt * speed_mult
            angle      += angle_delta

            # abs(cos(angle)) is edge-on at pi/2, 3pi/2, 5pi/2, ...  i.e. every pi radians
            # starting at pi/2.  Swap at every one of these — each unit gets exactly one
            # face-on presentation (the half-rotation between two consecutive edge-on points).
            # Shift by pi/2 so we count crossings of pi/2 + k*pi.
            OFFSET      = math.pi / 2
            PERIOD      = math.pi
            prev_count  = math.floor((prev_angle - OFFSET) / PERIOD)
            curr_count  = math.floor((angle      - OFFSET) / PERIOD)
            crossings   = curr_count - prev_count
            if crossings:
                unit_index = (unit_index + crossings) % n

            angle %= 2 * math.pi

        # --- Render ---
        draw_earthbound_bg(screen, bg_time)

        # Compute horizontal squish
        x_scale = spin_x_scale(angle)

        sprite      = sprites[unit_index]
        base_w      = int(SPRITE_RENDER_SIZE * disp_scale)
        base_h      = int(SPRITE_RENDER_SIZE * disp_scale)
        scaled_w    = max(1, int(base_w * x_scale))
        scaled_h    = base_h

        # Scale the sprite
        display_surf = pygame.transform.smoothscale(sprite, (scaled_w, scaled_h))

        # Blit sprite centered
        screen.blit(display_surf,
                    (center_x - scaled_w // 2,
                     center_y - scaled_h // 2))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
