#!/usr/bin/env python3
"""
MANDIBLE FOREMAN Animation Classes
Skill animations for the MANDIBLE FOREMAN unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, COLOR_DAMAGE, Particle
from boneglaive.graphical.sound_helper import play_sound

class JawClamp:
    """Animated mechanical jaws AND mandibles that clamp down on a target from all 4 directions."""
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.phase = "opening"  # opening, crushing, clamped, releasing
        self.timer = 0
        self.jaw_gap = 0  # Distance for vertical jaws (top/bottom)
        self.mandible_gap = 0  # Distance for horizontal mandibles (left/right)
        self.max_gap = 60  # Maximum opening
        self.active = True

        play_sound("mandible_attack_open")

    def update(self, delta_time):
        """Update jaw and mandible animation."""
        self.timer += delta_time

        if self.phase == "opening":
            # Jaws and mandibles open (0.2s)
            if self.timer < 0.2:
                progress = self.timer / 0.2
                self.jaw_gap = progress * self.max_gap
                self.mandible_gap = progress * self.max_gap
            else:
                self.phase = "crushing"
                self.timer = 0
                play_sound("mandible_attack_crush")

        elif self.phase == "crushing":
            # Jaws and mandibles slam shut (0.1s)
            if self.timer < 0.1:
                progress = self.timer / 0.1
                self.jaw_gap = self.max_gap * (1.0 - progress)
                self.mandible_gap = self.max_gap * (1.0 - progress)
            else:
                self.phase = "clamped"
                self.timer = 0
                self.jaw_gap = 0
                self.mandible_gap = 0

        elif self.phase == "clamped":
            # Hold closed (0.15s)
            if self.timer >= 0.15:
                self.phase = "releasing"
                self.timer = 0
                play_sound("mandible_attack_release")

        elif self.phase == "releasing":
            # Open and fade (0.15s)
            if self.timer < 0.15:
                progress = self.timer / 0.15
                self.jaw_gap = progress * 40
                self.mandible_gap = progress * 40
            else:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the mechanical jaws (vertical) and mandibles (horizontal)."""
        if not self.active:
            return

        # Calculate alpha based on phase
        if self.phase == "releasing":
            alpha = int(255 * (1.0 - self.timer / 0.15))
        else:
            alpha = 255

        # Draw vertical jaws (top and bottom)
        upper_jaw_y = self.target_y - self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, upper_jaw_y, True, alpha)

        lower_jaw_y = self.target_y + self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, lower_jaw_y, False, alpha)

        # Draw horizontal mandibles (left and right)
        left_mandible_x = self.target_x - self.mandible_gap
        self.draw_horizontal_mandible(surface, left_mandible_x, self.target_y, True, alpha)

        right_mandible_x = self.target_x + self.mandible_gap
        self.draw_horizontal_mandible(surface, right_mandible_x, self.target_y, False, alpha)

    def draw_vertical_jaw(self, surface, x, y, is_upper, alpha):
        """Draw vertical jaw (top or bottom) with sharp teeth."""
        jaw_width = 70
        jaw_height = 25

        jaw_surf = pygame.Surface((jaw_width, jaw_height), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        metal_highlight = (200, 200, 210, alpha)

        # Main jaw body
        pygame.draw.rect(jaw_surf, metal_dark, (0, 0, jaw_width, jaw_height))
        pygame.draw.rect(jaw_surf, metal_light, (0, 0, jaw_width, jaw_height), 2)

        # Sharp teeth pointing toward center
        num_teeth = 7
        tooth_width = jaw_width // num_teeth
        for i in range(num_teeth):
            tooth_x = i * tooth_width
            if is_upper:
                # Upper jaw teeth point downward
                points = [
                    (tooth_x + tooth_width // 2, jaw_height),
                    (tooth_x + 2, jaw_height - 12),
                    (tooth_x + tooth_width - 2, jaw_height - 12)
                ]
            else:
                # Lower jaw teeth point upward
                points = [
                    (tooth_x + tooth_width // 2, 0),
                    (tooth_x + 2, 12),
                    (tooth_x + tooth_width - 2, 12)
                ]
            pygame.draw.polygon(jaw_surf, metal_light, points)
            pygame.draw.polygon(jaw_surf, metal_highlight, points, 1)

        # Rivets
        for i in range(3):
            pygame.draw.circle(jaw_surf, (80, 80, 90, alpha), (15 + i * 20, jaw_height // 2), 3)

        surface.blit(jaw_surf, (int(x - jaw_width // 2), int(y - jaw_height // 2)))

    def draw_horizontal_mandible(self, surface, x, y, is_left, alpha):
        """Draw horizontal mandible shaped like a metal insect mandible - curved pincer."""
        mandible_length = 70
        mandible_width = 30

        mandible_surf = pygame.Surface((mandible_length, mandible_width), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (90, 90, 100, alpha)
        metal_light = (150, 150, 160, alpha)
        metal_highlight = (190, 190, 200, alpha)
        metal_accent = (120, 120, 130, alpha)

        if is_left:
            # Left mandible - curved pincer pointing right toward center
            # Main curved body (thick at base, tapering to sharp point)
            mandible_curve = [
                (0, mandible_width // 2),  # Base (left side, center)
                (10, 5),  # Upper curve
                (35, 2),  # Upper edge
                (60, mandible_width // 2 - 2),  # Tip upper
                (70, mandible_width // 2),  # Sharp tip
                (60, mandible_width // 2 + 2),  # Tip lower
                (35, mandible_width - 2),  # Lower edge
                (10, mandible_width - 5),  # Lower curve
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge (like insect mandible teeth)
            cutting_teeth = [40, 50, 55]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x + 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 8 + i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (60, mandible_width // 2 - 1), (70, mandible_width // 2), 2)

        else:
            # Right mandible - curved pincer pointing left toward center
            # Main curved body (mirror of left)
            mandible_curve = [
                (mandible_length, mandible_width // 2),  # Base (right side, center)
                (60, 5),  # Upper curve
                (35, 2),  # Upper edge
                (10, mandible_width // 2 - 2),  # Tip upper
                (0, mandible_width // 2),  # Sharp tip
                (10, mandible_width // 2 + 2),  # Tip lower
                (35, mandible_width - 2),  # Lower edge
                (60, mandible_width - 5),  # Lower curve
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge (like insect mandible teeth)
            cutting_teeth = [30, 20, 15]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x - 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 62 - i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (10, mandible_width // 2 - 1), (0, mandible_width // 2), 2)

        surface.blit(mandible_surf, (int(x - mandible_length // 2), int(y - mandible_width // 2)))


class JawRelease(JawClamp):
    """Jaw release animation - jaws spring open and fade away when trap is released."""
    def __init__(self, target_x, target_y):
        super().__init__(target_x, target_y)
        # Start closed and spring open
        self.phase = "spring_open"
        self.timer = 0
        self.jaw_gap = 0
        self.mandible_gap = 0
        self.max_gap = 50

    def update(self, delta_time):
        """Update jaw release animation - springs open and fades."""
        self.timer += delta_time

        if self.phase == "spring_open":
            # Jaws spring open quickly (0.2s)
            if self.timer < 0.2:
                progress = self.timer / 0.2
                # Ease-out for spring effect
                ease_progress = 1.0 - (1.0 - progress) ** 2
                self.jaw_gap = ease_progress * self.max_gap
                self.mandible_gap = ease_progress * self.max_gap
            else:
                self.phase = "fade"
                self.timer = 0

        elif self.phase == "fade":
            # Hold open and fade (0.25s)
            if self.timer < 0.25:
                # Keep jaws open during fade
                pass
            else:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the releasing jaws with fade effect."""
        if not self.active:
            return

        # Calculate alpha based on phase
        if self.phase == "fade":
            alpha = int(255 * (1.0 - self.timer / 0.25))
        else:
            alpha = 255

        # Draw vertical jaws (top and bottom)
        upper_jaw_y = self.target_y - self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, upper_jaw_y, True, alpha)

        lower_jaw_y = self.target_y + self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, lower_jaw_y, False, alpha)

        # Draw horizontal mandibles (left and right)
        left_mandible_x = self.target_x - self.mandible_gap
        self.draw_horizontal_mandible(surface, left_mandible_x, self.target_y, True, alpha)

        right_mandible_x = self.target_x + self.mandible_gap
        self.draw_horizontal_mandible(surface, right_mandible_x, self.target_y, False, alpha)


class ViseroyTrap:
    """Viseroy trap animation - jaws grind and chew the target over time, never releasing."""
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.phase = "snapping"  # snapping, grinding, clamped
        self.timer = 0
        self.jaw_gap = 60  # Start open
        self.mandible_gap = 60
        self.max_gap = 60
        self.grind_cycle = 0  # Track grinding cycles
        self.active = True
        self.damage_applied = False

        play_sound("viseroy_snap")

    def update(self, delta_time):
        """Update Viseroy trap animation with grinding motion."""
        self.timer += delta_time

        if self.phase == "snapping":
            # Jaws snap shut quickly (0.12s)
            if self.timer < 0.12:
                progress = self.timer / 0.12
                self.jaw_gap = 60 * (1.0 - progress)
                self.mandible_gap = 60 * (1.0 - progress)
            else:
                self.phase = "grinding"
                self.timer = 0
                self.jaw_gap = 0
                self.mandible_gap = 0
                play_sound("viseroy_grind")

        elif self.phase == "grinding":
            # Grinding chewing motion - open and close repeatedly (1.2s total)
            if self.timer < 1.2:
                # 4 grinding cycles (each 0.3s)
                cycle_time = self.timer % 0.3
                cycle_progress = cycle_time / 0.3

                # Pulsing chewing motion - open slightly then close
                if cycle_progress < 0.5:
                    # Opening phase of chew
                    open_amount = (cycle_progress / 0.5) * 20  # Open to 20 pixels
                    self.jaw_gap = open_amount
                    self.mandible_gap = open_amount
                else:
                    # Closing phase of chew
                    close_progress = (cycle_progress - 0.5) / 0.5
                    self.jaw_gap = 20 * (1.0 - close_progress)
                    self.mandible_gap = 20 * (1.0 - close_progress)

                self.grind_cycle = int(self.timer / 0.3)
            else:
                self.phase = "clamped"
                self.timer = 0
                self.jaw_gap = 0
                self.mandible_gap = 0
                play_sound("viseroy_clamp")

        elif self.phase == "clamped":
            # Hold clamped shut (0.3s) then fade
            if self.timer < 0.3:
                self.jaw_gap = 0
                self.mandible_gap = 0
            else:
                self.phase = "fading"
                self.timer = 0

        elif self.phase == "fading":
            # Fade out while staying closed (0.3s)
            if self.timer >= 0.3:
                self.active = False
                return False
            # Jaws stay closed (gap = 0) during fade

        return True

    def draw(self, surface):
        """Draw the Viseroy trap using the same jaw/mandible rendering."""
        if not self.active:
            return

        # Calculate alpha - fade out during "fading" phase while staying closed
        if self.phase == "fading":
            alpha = int(255 * (1.0 - self.timer / 0.3))
        else:
            alpha = 255

        # Draw vertical jaws (top and bottom)
        upper_jaw_y = self.target_y - self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, upper_jaw_y, True, alpha)

        lower_jaw_y = self.target_y + self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, lower_jaw_y, False, alpha)

        # Draw horizontal mandibles (left and right)
        left_mandible_x = self.target_x - self.mandible_gap
        self.draw_horizontal_mandible(surface, left_mandible_x, self.target_y, True, alpha)

        right_mandible_x = self.target_x + self.mandible_gap
        self.draw_horizontal_mandible(surface, right_mandible_x, self.target_y, False, alpha)

    def draw_vertical_jaw(self, surface, x, y, is_upper, alpha):
        """Draw vertical jaw (reusing JawClamp's method)."""
        jaw_width = 70
        jaw_height = 25

        jaw_surf = pygame.Surface((jaw_width, jaw_height), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        metal_highlight = (200, 200, 210, alpha)

        # Main jaw body
        pygame.draw.rect(jaw_surf, metal_dark, (0, 0, jaw_width, jaw_height))
        pygame.draw.rect(jaw_surf, metal_light, (0, 0, jaw_width, jaw_height), 2)

        # Sharp teeth pointing toward center
        num_teeth = 7
        tooth_width = jaw_width // num_teeth
        for i in range(num_teeth):
            tooth_x = i * tooth_width
            if is_upper:
                # Upper jaw teeth point downward
                tooth_points = [
                    (tooth_x + tooth_width // 2, jaw_height),
                    (tooth_x + 2, jaw_height - 12),
                    (tooth_x + tooth_width - 2, jaw_height - 12)
                ]
            else:
                # Lower jaw teeth point upward
                tooth_points = [
                    (tooth_x + tooth_width // 2, 0),
                    (tooth_x + 2, 12),
                    (tooth_x + tooth_width - 2, 12)
                ]
            pygame.draw.polygon(jaw_surf, metal_light, tooth_points)
            pygame.draw.polygon(jaw_surf, metal_highlight, tooth_points, 1)

        # Rivets
        for i in range(3):
            pygame.draw.circle(jaw_surf, (80, 80, 90, alpha), (15 + i * 20, jaw_height // 2), 3)

        surface.blit(jaw_surf, (int(x - jaw_width // 2), int(y - jaw_height // 2)))

    def draw_horizontal_mandible(self, surface, x, y, is_left, alpha):
        """Draw horizontal mandible (reusing JawClamp's method)."""
        mandible_length = 70
        mandible_width = 30

        mandible_surf = pygame.Surface((mandible_length, mandible_width), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (90, 90, 100, alpha)
        metal_light = (150, 150, 160, alpha)
        metal_highlight = (190, 190, 200, alpha)
        metal_accent = (120, 120, 130, alpha)

        if is_left:
            # Left mandible - curved pincer pointing right toward center
            mandible_curve = [
                (0, mandible_width // 2),
                (10, 5),
                (35, 2),
                (60, mandible_width // 2 - 2),
                (70, mandible_width // 2),
                (60, mandible_width // 2 + 2),
                (35, mandible_width - 2),
                (10, mandible_width - 5),
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge
            cutting_teeth = [40, 50, 55]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x + 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 8 + i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (60, mandible_width // 2 - 1), (70, mandible_width // 2), 2)

        else:
            # Right mandible - curved pincer pointing left toward center
            mandible_curve = [
                (mandible_length, mandible_width // 2),
                (60, 5),
                (35, 2),
                (10, mandible_width // 2 - 2),
                (0, mandible_width // 2),
                (10, mandible_width // 2 + 2),
                (35, mandible_width - 2),
                (60, mandible_width - 5),
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge
            cutting_teeth = [30, 20, 15]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x - 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 62 - i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (10, mandible_width // 2 - 1), (0, mandible_width // 2), 2)

        surface.blit(mandible_surf, (int(x - mandible_length // 2), int(y - mandible_width // 2)))


class JawTighten:
    """Quick jaw tightening animation for periodic trap tick damage."""
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.phase = "squeeze"  # squeeze, hold, relax, fade
        self.timer = 0
        self.jaw_gap = 8  # Start with small resting gap
        self.mandible_gap = 8
        self.active = True

        play_sound("viseroy_tick_squeeze")

    def update(self, delta_time):
        """Update jaw tightening animation."""
        self.timer += delta_time

        if self.phase == "squeeze":
            # Jaws squeeze tighter (0.15s)
            if self.timer < 0.15:
                progress = self.timer / 0.15
                # Ease-in for crushing pressure
                ease = progress * progress
                self.jaw_gap = 8 * (1.0 - ease)
                self.mandible_gap = 8 * (1.0 - ease)
            else:
                self.phase = "hold"
                self.timer = 0
                self.jaw_gap = 0
                self.mandible_gap = 0

        elif self.phase == "hold":
            # Hold maximum pressure (0.1s)
            if self.timer >= 0.1:
                self.phase = "relax"
                self.timer = 0

        elif self.phase == "relax":
            # Return to resting position (0.15s)
            if self.timer < 0.15:
                progress = self.timer / 0.15
                # Ease-out for spring back
                ease = 1.0 - (1.0 - progress) ** 2
                self.jaw_gap = ease * 8
                self.mandible_gap = ease * 8
            else:
                self.phase = "fade"
                self.timer = 0
                self.jaw_gap = 8
                self.mandible_gap = 8

        elif self.phase == "fade":
            # Fade out (0.1s)
            if self.timer >= 0.1:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the tightening jaws."""
        if not self.active:
            return

        # Calculate alpha based on phase
        if self.phase == "fade":
            alpha = int(255 * (1.0 - self.timer / 0.1))
        else:
            alpha = 255

        # Pulsing red tint during squeeze/hold for damage indication
        if self.phase in ["squeeze", "hold"]:
            pulse_intensity = 0.3 if self.phase == "hold" else (self.timer / 0.15) * 0.3

        # Draw vertical jaws (top and bottom)
        upper_jaw_y = self.target_y - self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, upper_jaw_y, True, alpha)

        lower_jaw_y = self.target_y + self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, lower_jaw_y, False, alpha)

        # Draw horizontal mandibles (left and right)
        left_mandible_x = self.target_x - self.mandible_gap
        self.draw_horizontal_mandible(surface, left_mandible_x, self.target_y, True, alpha)

        right_mandible_x = self.target_x + self.mandible_gap
        self.draw_horizontal_mandible(surface, right_mandible_x, self.target_y, False, alpha)

        # Draw pressure particles during squeeze
        if self.phase == "squeeze" or self.phase == "hold":
            import random
            # Small spark particles at jaw contact points
            for _ in range(2):
                offset_x = random.uniform(-5, 5)
                offset_y = random.uniform(-5, 5)
                spark_x = self.target_x + offset_x
                spark_y = self.target_y + offset_y
                spark_size = random.randint(2, 4)
                spark_alpha = int(alpha * 0.8)
                pygame.draw.circle(surface, (255, 200, 100, spark_alpha),
                                 (int(spark_x), int(spark_y)), spark_size)

    def draw_vertical_jaw(self, surface, x, y, is_upper, alpha):
        """Draw vertical jaw (reusing JawClamp's method)."""
        jaw_width = 70
        jaw_height = 25

        jaw_surf = pygame.Surface((jaw_width, jaw_height), pygame.SRCALPHA)

        # Metal colors with red tint during pressure
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        metal_highlight = (200, 200, 210, alpha)

        # Main jaw body
        pygame.draw.rect(jaw_surf, metal_dark, (0, 0, jaw_width, jaw_height))
        pygame.draw.rect(jaw_surf, metal_light, (0, 0, jaw_width, jaw_height), 2)

        # Sharp teeth pointing toward center
        num_teeth = 7
        tooth_width = jaw_width // num_teeth
        for i in range(num_teeth):
            tooth_x = i * tooth_width
            if is_upper:
                # Upper jaw teeth point downward
                points = [
                    (tooth_x + tooth_width // 2, jaw_height),
                    (tooth_x + 2, jaw_height - 12),
                    (tooth_x + tooth_width - 2, jaw_height - 12)
                ]
            else:
                # Lower jaw teeth point upward
                points = [
                    (tooth_x + tooth_width // 2, 0),
                    (tooth_x + 2, 12),
                    (tooth_x + tooth_width - 2, 12)
                ]
            pygame.draw.polygon(jaw_surf, metal_light, points)
            pygame.draw.polygon(jaw_surf, metal_highlight, points, 1)

        # Rivets
        for i in range(3):
            pygame.draw.circle(jaw_surf, (80, 80, 90, alpha), (15 + i * 20, jaw_height // 2), 3)

        surface.blit(jaw_surf, (int(x - jaw_width // 2), int(y - jaw_height // 2)))

    def draw_horizontal_mandible(self, surface, x, y, is_left, alpha):
        """Draw horizontal mandible (reusing JawClamp's method)."""
        mandible_length = 70
        mandible_width = 30

        mandible_surf = pygame.Surface((mandible_length, mandible_width), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (90, 90, 100, alpha)
        metal_light = (150, 150, 160, alpha)
        metal_highlight = (190, 190, 200, alpha)
        metal_accent = (120, 120, 130, alpha)

        if is_left:
            # Left mandible - curved pincer pointing right toward center
            mandible_curve = [
                (0, mandible_width // 2),
                (10, 5),
                (35, 2),
                (60, mandible_width // 2 - 2),
                (70, mandible_width // 2),
                (60, mandible_width // 2 + 2),
                (35, mandible_width - 2),
                (10, mandible_width - 5),
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge
            cutting_teeth = [40, 50, 55]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x + 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 8 + i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (60, mandible_width // 2 - 1), (70, mandible_width // 2), 2)

        else:
            # Right mandible - curved pincer pointing left toward center
            mandible_curve = [
                (mandible_length, mandible_width // 2),
                (60, 5),
                (35, 2),
                (10, mandible_width // 2 - 2),
                (0, mandible_width // 2),
                (10, mandible_width // 2 + 2),
                (35, mandible_width - 2),
                (60, mandible_width - 5),
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge
            cutting_teeth = [30, 20, 15]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x - 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 62 - i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (10, mandible_width // 2 - 1), (0, mandible_width // 2), 2)

        surface.blit(mandible_surf, (int(x - mandible_length // 2), int(y - mandible_width // 2)))


class ViseroyRelease:
    """Animation for releasing a victim from Viseroy trap - jaws open dramatically."""
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.phase = "opening"  # opening, releasing
        self.timer = 0
        self.jaw_gap = 0  # Start closed
        self.mandible_gap = 0
        self.max_gap = 70  # Open wider than initial snap
        self.active = True

        play_sound("discharge_spring")

    def update(self, delta_time):
        """Update release animation - jaws spring open."""
        self.timer += delta_time

        if self.phase == "opening":
            # Jaws spring open quickly with slight overshoot (0.25s)
            if self.timer < 0.25:
                progress = self.timer / 0.25
                # Ease-out with slight overshoot
                overshoot = 1.0 + 0.15 * math.sin(progress * math.pi)
                self.jaw_gap = progress * self.max_gap * overshoot
                self.mandible_gap = progress * self.max_gap * overshoot
            else:
                self.phase = "releasing"
                self.timer = 0

        elif self.phase == "releasing":
            # Fade out while staying open (0.2s)
            if self.timer >= 0.2:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the release animation with jaws opening."""
        if not self.active:
            return

        # Calculate alpha - fade during releasing phase
        if self.phase == "releasing":
            alpha = int(255 * (1.0 - self.timer / 0.2))
        else:
            alpha = 255

        # Draw vertical jaws (top and bottom)
        upper_jaw_y = self.target_y - self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, upper_jaw_y, True, alpha)

        lower_jaw_y = self.target_y + self.jaw_gap
        self.draw_vertical_jaw(surface, self.target_x, lower_jaw_y, False, alpha)

        # Draw horizontal mandibles (left and right)
        left_mandible_x = self.target_x - self.mandible_gap
        self.draw_horizontal_mandible(surface, left_mandible_x, self.target_y, True, alpha)

        right_mandible_x = self.target_x + self.mandible_gap
        self.draw_horizontal_mandible(surface, right_mandible_x, self.target_y, False, alpha)

    def draw_vertical_jaw(self, surface, x, y, is_upper, alpha):
        """Draw vertical jaw (reusing same method)."""
        jaw_width = 70
        jaw_height = 25

        jaw_surf = pygame.Surface((jaw_width, jaw_height), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        metal_highlight = (200, 200, 210, alpha)

        # Main jaw body
        pygame.draw.rect(jaw_surf, metal_dark, (0, 0, jaw_width, jaw_height))
        pygame.draw.rect(jaw_surf, metal_light, (0, 0, jaw_width, jaw_height), 2)

        # Sharp teeth pointing toward center
        num_teeth = 7
        tooth_width = jaw_width // num_teeth
        for i in range(num_teeth):
            tooth_x = i * tooth_width
            if is_upper:
                # Upper jaw teeth point downward
                tooth_points = [
                    (tooth_x + tooth_width // 2, jaw_height),
                    (tooth_x + 2, jaw_height - 12),
                    (tooth_x + tooth_width - 2, jaw_height - 12)
                ]
            else:
                # Lower jaw teeth point upward
                tooth_points = [
                    (tooth_x + tooth_width // 2, 0),
                    (tooth_x + 2, 12),
                    (tooth_x + tooth_width - 2, 12)
                ]
            pygame.draw.polygon(jaw_surf, metal_light, tooth_points)
            pygame.draw.polygon(jaw_surf, metal_highlight, tooth_points, 1)

        # Rivets
        for i in range(3):
            pygame.draw.circle(jaw_surf, (80, 80, 90, alpha), (15 + i * 20, jaw_height // 2), 3)

        surface.blit(jaw_surf, (int(x - jaw_width // 2), int(y - jaw_height // 2)))

    def draw_horizontal_mandible(self, surface, x, y, is_left, alpha):
        """Draw horizontal mandible (reusing same method)."""
        mandible_length = 70
        mandible_width = 30

        mandible_surf = pygame.Surface((mandible_length, mandible_width), pygame.SRCALPHA)

        # Metal colors
        metal_dark = (90, 90, 100, alpha)
        metal_light = (150, 150, 160, alpha)
        metal_highlight = (190, 190, 200, alpha)
        metal_accent = (120, 120, 130, alpha)

        if is_left:
            # Left mandible - curved pincer pointing right toward center
            mandible_curve = [
                (0, mandible_width // 2),
                (10, 5),
                (35, 2),
                (60, mandible_width // 2 - 2),
                (70, mandible_width // 2),
                (60, mandible_width // 2 + 2),
                (35, mandible_width - 2),
                (10, mandible_width - 5),
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge
            cutting_teeth = [40, 50, 55]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x + 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 8 + i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (60, mandible_width // 2 - 1), (70, mandible_width // 2), 2)

        else:
            # Right mandible - curved pincer pointing left toward center
            mandible_curve = [
                (mandible_length, mandible_width // 2),
                (60, 5),
                (35, 2),
                (10, mandible_width // 2 - 2),
                (0, mandible_width // 2),
                (10, mandible_width // 2 + 2),
                (35, mandible_width - 2),
                (60, mandible_width - 5),
            ]
            pygame.draw.polygon(mandible_surf, metal_dark, mandible_curve)
            pygame.draw.polygon(mandible_surf, metal_light, mandible_curve, 2)

            # Inner serrated cutting edge
            cutting_teeth = [30, 20, 15]
            for tooth_x in cutting_teeth:
                tooth_points = [
                    (tooth_x, mandible_width // 2 - 3),
                    (tooth_x - 5, mandible_width // 2),
                    (tooth_x, mandible_width // 2 + 3)
                ]
                pygame.draw.polygon(mandible_surf, metal_highlight, tooth_points)

            # Segmented exoskeleton plates
            for i in range(4):
                segment_x = 62 - i * 12
                pygame.draw.line(mandible_surf, metal_accent,
                               (segment_x, 8), (segment_x, mandible_width - 8), 2)

            # Sharp tip highlight
            pygame.draw.line(mandible_surf, metal_highlight,
                           (10, mandible_width // 2 - 1), (0, mandible_width // 2), 2)

        surface.blit(mandible_surf, (int(x - mandible_length // 2), int(y - mandible_width // 2)))


class SiteInspectionBuff:
    """Visual buff indicator for units receiving Site Inspection bonuses."""
    def __init__(self, target_x, target_y, is_full_buff):
        self.target_x = target_x
        self.target_y = target_y
        self.is_full_buff = is_full_buff  # True = full buff, False = partial buff
        self.phase = "appearing"  # appearing, pulsing, fading
        self.timer = 0
        self.ring_radius = 0
        self.active = True
        self.pulse_alpha = 255

    def update(self, delta_time):
        """Update buff indicator animation."""
        self.timer += delta_time

        if self.phase == "waiting":
            # Waiting for trigger delay to elapse
            if self.timer >= 0:
                self.phase = "appearing"
                self.timer = 0
            return True

        if self.phase == "appearing":
            # Ring expands outward (0.3s)
            if self.timer < 0.3:
                progress = self.timer / 0.3
                if self.is_full_buff:
                    self.ring_radius = progress * 35  # Larger for full buff
                else:
                    self.ring_radius = progress * 25  # Smaller for partial
            else:
                self.phase = "pulsing"
                self.timer = 0

        elif self.phase == "pulsing":
            # Pulsing glow (0.8s total, 2 pulses)
            if self.timer < 0.8:
                pulse_cycle = (math.sin(self.timer * 2 * math.pi * 2.5) + 1) / 2  # 2 pulses
                self.pulse_alpha = int(150 + pulse_cycle * 105)
            else:
                self.phase = "fading"
                self.timer = 0

        elif self.phase == "fading":
            # Fade out (0.3s)
            if self.timer < 0.3:
                fade_progress = self.timer / 0.3
                self.pulse_alpha = int(255 * (1.0 - fade_progress))
            else:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the buff indicator."""
        if not self.active or self.pulse_alpha == 0:
            return

        if self.is_full_buff:
            # FULL BUFF - Green and blue tactical display with movement arrows
            primary_color = (0, 255, 100, self.pulse_alpha)
            secondary_color = (100, 200, 255, self.pulse_alpha)

            # Outer ring
            if self.ring_radius > 0:
                pygame.draw.circle(surface, primary_color,
                                 (int(self.target_x), int(self.target_y)),
                                 int(self.ring_radius), 3)
                pygame.draw.circle(surface, secondary_color,
                                 (int(self.target_x), int(self.target_y)),
                                 int(self.ring_radius - 5), 2)

            # Four directional arrows (indicating movement boost)
            if self.phase != "appearing":
                arrow_distance = 25
                arrow_size = 8
                directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Up, Right, Down, Left

                for dx, dy in directions:
                    arrow_x = self.target_x + dx * arrow_distance
                    arrow_y = self.target_y + dy * arrow_distance

                    # Arrow shaft
                    pygame.draw.line(surface, secondary_color,
                                   (self.target_x + dx * 10, self.target_y + dy * 10),
                                   (arrow_x, arrow_y), 2)

                    # Arrow head
                    if dx == 0:  # Vertical arrows
                        head_points = [
                            (arrow_x, arrow_y),
                            (arrow_x - arrow_size//2, arrow_y - dy * arrow_size),
                            (arrow_x + arrow_size//2, arrow_y - dy * arrow_size)
                        ]
                    else:  # Horizontal arrows
                        head_points = [
                            (arrow_x, arrow_y),
                            (arrow_x - dx * arrow_size, arrow_y - arrow_size//2),
                            (arrow_x - dx * arrow_size, arrow_y + arrow_size//2)
                        ]
                    pygame.draw.polygon(surface, secondary_color, head_points)

            # Center tactical crosshair
            if self.phase != "appearing":
                cross_size = 12
                # Diagonal lines forming X
                pygame.draw.line(surface, primary_color,
                               (self.target_x - cross_size, self.target_y - cross_size),
                               (self.target_x + cross_size, self.target_y + cross_size), 2)
                pygame.draw.line(surface, primary_color,
                               (self.target_x + cross_size, self.target_y - cross_size),
                               (self.target_x - cross_size, self.target_y + cross_size), 2)
                # Center dot
                pygame.draw.circle(surface, (255, 255, 100, self.pulse_alpha),
                                 (int(self.target_x), int(self.target_y)), 3)

        else:
            # PARTIAL BUFF - Orange/amber warning indicator (attack boost only)
            primary_color = (255, 150, 0, self.pulse_alpha)
            secondary_color = (255, 200, 100, self.pulse_alpha)

            # Single ring (smaller, less dramatic)
            if self.ring_radius > 0:
                pygame.draw.circle(surface, primary_color,
                                 (int(self.target_x), int(self.target_y)),
                                 int(self.ring_radius), 2)

            # Danger/attack indicator - triangular warning markers
            if self.phase != "appearing":
                marker_distance = 18
                marker_size = 6
                angles = [0, 120, 240]  # Three warning triangles evenly spaced

                for angle_deg in angles:
                    angle_rad = math.radians(angle_deg)
                    marker_x = self.target_x + math.cos(angle_rad) * marker_distance
                    marker_y = self.target_y + math.sin(angle_rad) * marker_distance

                    # Warning triangle pointing outward
                    offset_x = math.cos(angle_rad) * marker_size
                    offset_y = math.sin(angle_rad) * marker_size
                    perp_x = -math.sin(angle_rad) * marker_size * 0.6
                    perp_y = math.cos(angle_rad) * marker_size * 0.6

                    triangle_points = [
                        (marker_x + offset_x, marker_y + offset_y),
                        (marker_x - offset_x//2 + perp_x, marker_y - offset_y//2 + perp_y),
                        (marker_x - offset_x//2 - perp_x, marker_y - offset_y//2 - perp_y)
                    ]
                    pygame.draw.polygon(surface, primary_color, triangle_points)
                    pygame.draw.polygon(surface, secondary_color, triangle_points, 1)

            # Center attack symbol (sword/blade icon)
            if self.phase != "appearing":
                blade_length = 10
                # Vertical blade
                pygame.draw.line(surface, secondary_color,
                               (self.target_x, self.target_y - blade_length),
                               (self.target_x, self.target_y + blade_length), 3)
                # Crossguard
                pygame.draw.line(surface, primary_color,
                               (self.target_x - 6, self.target_y - 2),
                               (self.target_x + 6, self.target_y - 2), 2)
                # Blade tip
                pygame.draw.polygon(surface, primary_color,
                                  [(self.target_x, self.target_y - blade_length - 3),
                                   (self.target_x - 3, self.target_y - blade_length),
                                   (self.target_x + 3, self.target_y - blade_length)])


class SiteInspectionScan:
    """Animation for SITE INSPECTION - laser level scanning a 3x3 grid."""
    def __init__(self, center_x, center_y, camera=None):
        # Get tile size from camera (or fallback to default)
        if camera:
            tile_size = camera.tile_size
        else:
            tile_size = TILE_SIZE

        # Coordinates are already properly centered from grid_to_screen conversion
        # No need to snap - the animation factory already handles grid offset
        self.center_x = center_x
        self.center_y = center_y
        self.phase = "deploying"  # deploying, scanning, complete
        self.timer = 0
        self.scan_progress = 0  # 0 to 1
        self.grid_size = tile_size  # Size of each grid cell
        self.active = True
        self.laser_alpha = 0
        self.camera = camera

        play_sound("site_inspection_deploy")

    def update(self, delta_time):
        """Update site inspection animation."""
        self.timer += delta_time

        if self.phase == "deploying":
            # Lasers fade in (0.2s)
            if self.timer < 0.2:
                self.laser_alpha = int(255 * (self.timer / 0.2))
            else:
                self.phase = "scanning"
                self.timer = 0
                self.laser_alpha = 255
                play_sound("site_inspection_scan")

        elif self.phase == "scanning":
            # Scan across the grid (1.0s)
            if self.timer < 1.0:
                self.scan_progress = self.timer / 1.0
            else:
                self.phase = "complete"
                self.timer = 0

        elif self.phase == "complete":
            # Hold complete state briefly then fade (0.5s)
            if self.timer < 0.3:
                # Hold fully visible
                pass
            elif self.timer < 0.5:
                # Fade out
                fade_progress = (self.timer - 0.3) / 0.2
                self.laser_alpha = int(255 * (1.0 - fade_progress))
            else:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the laser level scanning grid."""
        if not self.active or self.laser_alpha == 0:
            return

        # Define 3x3 grid centered on target
        grid_offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0), (0,  0), (1,  0),
            (-1,  1), (0,  1), (1,  1)
        ]

        # Laser colors
        laser_red = (255, 0, 0, self.laser_alpha)
        laser_bright = (255, 100, 100, self.laser_alpha)
        grid_line_color = (255, 50, 50, min(self.laser_alpha, 180))

        # Draw horizontal and vertical laser beams forming grid
        for dx, dy in grid_offsets:
            cell_x = self.center_x + dx * self.grid_size
            cell_y = self.center_y + dy * self.grid_size

            # Draw grid cell outline
            if self.phase != "deploying":
                rect_surf = pygame.Surface((self.grid_size, self.grid_size), pygame.SRCALPHA)
                pygame.draw.rect(rect_surf, grid_line_color,
                               (0, 0, self.grid_size, self.grid_size), 2)
                surface.blit(rect_surf, (int(cell_x - self.grid_size // 2),
                                        int(cell_y - self.grid_size // 2)))

        # During scanning phase, draw sweeping laser line
        if self.phase == "scanning":
            # Vertical sweep from top to bottom
            sweep_y = self.center_y - self.grid_size * 1.5 + self.scan_progress * (self.grid_size * 3)

            # Draw horizontal scanning line
            pygame.draw.line(surface, laser_bright,
                           (self.center_x - self.grid_size * 1.5, sweep_y),
                           (self.center_x + self.grid_size * 1.5, sweep_y), 3)

            # Draw vertical scanning line (perpendicular)
            sweep_x = self.center_x - self.grid_size * 1.5 + self.scan_progress * (self.grid_size * 3)
            pygame.draw.line(surface, laser_bright,
                           (sweep_x, self.center_y - self.grid_size * 1.5),
                           (sweep_x, self.center_y + self.grid_size * 1.5), 3)

            # Crosshair at intersection
            cross_size = 8
            pygame.draw.line(surface, (255, 255, 100, self.laser_alpha),
                           (sweep_x - cross_size, sweep_y),
                           (sweep_x + cross_size, sweep_y), 2)
            pygame.draw.line(surface, (255, 255, 100, self.laser_alpha),
                           (sweep_x, sweep_y - cross_size),
                           (sweep_x, sweep_y + cross_size), 2)

        # Draw corner markers for the 3x3 area
        if self.phase == "complete" or (self.phase == "scanning" and self.scan_progress > 0.7):
            corner_size = 6
            corners = [
                (self.center_x - self.grid_size * 1.5, self.center_y - self.grid_size * 1.5),
                (self.center_x + self.grid_size * 1.5, self.center_y - self.grid_size * 1.5),
                (self.center_x - self.grid_size * 1.5, self.center_y + self.grid_size * 1.5),
                (self.center_x + self.grid_size * 1.5, self.center_y + self.grid_size * 1.5),
            ]

            for cx, cy in corners:
                # L-shaped corner markers
                pygame.draw.line(surface, (0, 255, 0, self.laser_alpha),
                               (cx - corner_size, cy), (cx + corner_size, cy), 2)
                pygame.draw.line(surface, (0, 255, 0, self.laser_alpha),
                               (cx, cy - corner_size), (cx, cy + corner_size), 2)

        # Draw center crosshair (always visible during scan)
        if self.phase != "deploying":
            center_cross_size = 10
            pygame.draw.line(surface, (255, 200, 0, self.laser_alpha),
                           (self.center_x - center_cross_size, self.center_y),
                           (self.center_x + center_cross_size, self.center_y), 3)
            pygame.draw.line(surface, (255, 200, 0, self.laser_alpha),
                           (self.center_x, self.center_y - center_cross_size),
                           (self.center_x, self.center_y + center_cross_size), 3)


class SiteInspectionScanUpgraded:
    """
    UPGRADED Site Inspection animation - Advanced tactical survey with holographic projection.
    Features dual-pass scanning, holographic terrain mapping, and tactical overlay system.
    """
    def __init__(self, center_x, center_y, camera=None):
        # Get tile size from camera (or fallback to default)
        if camera:
            tile_size = camera.tile_size
        else:
            tile_size = TILE_SIZE

        self.center_x = center_x
        self.center_y = center_y
        self.phase = "initialization"  # initialization, first_scan, hologram_projection, second_scan, tactical_overlay, complete
        self.timer = 0
        self.scan_progress = 0  # 0 to 1
        self.grid_size = tile_size
        self.active = True
        self.laser_alpha = 0
        self.camera = camera

        # Dual-pass scan tracking
        self.scan_pass = 0  # 0 or 1 (two passes)

        # Holographic grid nodes - 3x3 grid positions
        self.grid_nodes = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                node_x = center_x + dx * tile_size
                node_y = center_y + dy * tile_size
                self.grid_nodes.append({
                    'x': node_x,
                    'y': node_y,
                    'dx': dx,
                    'dy': dy,
                    'activation': 0.0,  # 0 to 1
                    'pulse_phase': random.uniform(0, math.pi * 2)
                })

        # Data flow particles - flowing between nodes
        self.data_particles = []

        # Tactical markers that appear during overlay phase
        self.tactical_markers = []

        play_sound("site_inspection_deploy")

    def update(self, delta_time):
        """Update upgraded site inspection animation."""
        self.timer += delta_time

        if self.phase == "initialization":
            # Deploy scanner array (0.3s) - corners activate first
            if self.timer < 0.3:
                progress = self.timer / 0.3
                self.laser_alpha = int(255 * progress)

                # Activate corner nodes first, then edges, then center
                for node in self.grid_nodes:
                    distance_from_corner = abs(node['dx']) + abs(node['dy'])
                    if distance_from_corner == 2:  # Corners
                        node['activation'] = min(1.0, progress * 1.5)
                    elif distance_from_corner == 1:  # Edges
                        node['activation'] = min(1.0, max(0, (progress - 0.3) * 2.0))
                    else:  # Center
                        node['activation'] = min(1.0, max(0, (progress - 0.6) * 2.5))
            else:
                self.phase = "first_scan"
                self.timer = 0
                self.laser_alpha = 255
                for node in self.grid_nodes:
                    node['activation'] = 1.0

        elif self.phase == "first_scan":
            # First rapid scan pass - horizontal and vertical sweeps simultaneously (0.6s)
            if self.timer < 0.6:
                self.scan_progress = self.timer / 0.6

                # Spawn data particles during scan
                if random.random() < 0.3:
                    # Pick random node pair to connect
                    node_a = random.choice(self.grid_nodes)
                    node_b = random.choice(self.grid_nodes)
                    if node_a != node_b:
                        self.data_particles.append({
                            'start_x': node_a['x'],
                            'start_y': node_a['y'],
                            'end_x': node_b['x'],
                            'end_y': node_b['y'],
                            'progress': 0.0,
                            'speed': random.uniform(1.5, 2.5),
                            'color': (255, 50, 50)  # Red data flow to match laser color
                        })
            else:
                self.phase = "hologram_projection"
                self.timer = 0
                play_sound("site_inspection_hologram")

        elif self.phase == "hologram_projection":
            # Project holographic terrain map (0.4s)
            if self.timer < 0.4:
                progress = self.timer / 0.4

                # All nodes pulse in sync
                for node in self.grid_nodes:
                    node['pulse_phase'] += delta_time * 8

                # Spawn more data particles - denser network
                if random.random() < 0.5:
                    node_a = random.choice(self.grid_nodes)
                    node_b = random.choice(self.grid_nodes)
                    if node_a != node_b:
                        self.data_particles.append({
                            'start_x': node_a['x'],
                            'start_y': node_a['y'],
                            'end_x': node_b['x'],
                            'end_y': node_b['y'],
                            'progress': 0.0,
                            'speed': random.uniform(2.0, 3.5),
                            'color': (255, 100, 100)  # Brighter red for hologram phase
                        })
            else:
                self.phase = "second_scan"
                self.timer = 0
                self.scan_pass = 1

        elif self.phase == "second_scan":
            # Second scan pass - diagonal sweeps for comprehensive coverage (0.5s)
            if self.timer < 0.5:
                self.scan_progress = self.timer / 0.5

                # Even more data particles - analysis complete
                if random.random() < 0.4:
                    node_a = random.choice(self.grid_nodes)
                    node_b = random.choice(self.grid_nodes)
                    if node_a != node_b:
                        self.data_particles.append({
                            'start_x': node_a['x'],
                            'start_y': node_a['y'],
                            'end_x': node_b['x'],
                            'end_y': node_b['y'],
                            'progress': 0.0,
                            'speed': random.uniform(2.5, 4.0),
                            'color': (255, 200, 0)  # Yellow for second scan (matches center crosshair)
                        })
            else:
                self.phase = "tactical_overlay"
                self.timer = 0
                play_sound("site_inspection_overlay")

                # Create tactical markers at each node
                for node in self.grid_nodes:
                    self.tactical_markers.append({
                        'x': node['x'],
                        'y': node['y'],
                        'alpha': 0,
                        'size': 0
                    })

        elif self.phase == "tactical_overlay":
            # Display tactical analysis overlay (0.5s display + 0.3s fade)
            if self.timer < 0.5:
                # Fade in tactical markers
                progress = min(1.0, self.timer / 0.2)
                for marker in self.tactical_markers:
                    marker['alpha'] = int(255 * progress)
                    marker['size'] = progress * 25

                # Continue node pulsing
                for node in self.grid_nodes:
                    node['pulse_phase'] += delta_time * 5
            elif self.timer < 0.8:
                # Fade out
                fade_progress = (self.timer - 0.5) / 0.3
                fade_alpha = int(255 * (1.0 - fade_progress))
                self.laser_alpha = fade_alpha
                for marker in self.tactical_markers:
                    marker['alpha'] = fade_alpha
                for node in self.grid_nodes:
                    node['activation'] = 1.0 - fade_progress
            else:
                self.phase = "complete"
                self.timer = 0

        elif self.phase == "complete":
            # Brief hold then deactivate (0.1s)
            if self.timer >= 0.1:
                self.active = False
                return False

        # Update data particles
        updated_particles = []
        for particle in self.data_particles:
            particle['progress'] += delta_time * particle['speed']
            if particle['progress'] < 1.0:
                updated_particles.append(particle)
        self.data_particles = updated_particles

        return True

    def draw(self, surface):
        """Draw the upgraded site inspection animation."""
        if not self.active:
            return

        # Draw 3x3 grid structure
        grid_offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0), (0,  0), (1,  0),
            (-1,  1), (0,  1), (1,  1)
        ]

        # Colors - matching base Site Inspection color scheme
        laser_red = (255, 0, 0, self.laser_alpha)
        laser_bright = (255, 100, 100, self.laser_alpha)
        laser_yellow = (255, 200, 0, self.laser_alpha)
        grid_line_color = (255, 50, 50, min(self.laser_alpha, 200))

        # Draw grid framework
        if self.phase != "initialization":
            # Horizontal lines
            for i in range(-1, 2):
                y_pos = self.center_y + i * self.grid_size
                pygame.draw.line(surface, grid_line_color,
                               (self.center_x - self.grid_size * 1.5, y_pos),
                               (self.center_x + self.grid_size * 1.5, y_pos), 2)

            # Vertical lines
            for i in range(-1, 2):
                x_pos = self.center_x + i * self.grid_size
                pygame.draw.line(surface, grid_line_color,
                               (x_pos, self.center_y - self.grid_size * 1.5),
                               (x_pos, self.center_y + self.grid_size * 1.5), 2)

        # Draw holographic nodes with pulsing effect
        for node in self.grid_nodes:
            if node['activation'] > 0:
                # Pulsing glow
                pulse = (math.sin(node['pulse_phase']) + 1) / 2
                node_alpha = int(self.laser_alpha * node['activation'])
                glow_size = int(8 + pulse * 4)

                # Outer glow
                glow_surf = pygame.Surface((glow_size * 4, glow_size * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 50, 50, int(node_alpha * 0.3)),
                                 (glow_size * 2, glow_size * 2), glow_size * 2)
                glow_rect = glow_surf.get_rect(center=(int(node['x']), int(node['y'])))
                surface.blit(glow_surf, glow_rect)

                # Core node - red laser style
                pygame.draw.circle(surface, (255, 100, 100, node_alpha),
                                 (int(node['x']), int(node['y'])), glow_size)
                pygame.draw.circle(surface, (255, 255, 100, node_alpha),  # Yellow center
                                 (int(node['x']), int(node['y'])), int(glow_size * 0.5))

        # Draw data flow particles - connections between nodes
        for particle in self.data_particles:
            current_x = particle['start_x'] + (particle['end_x'] - particle['start_x']) * particle['progress']
            current_y = particle['start_y'] + (particle['end_y'] - particle['start_y']) * particle['progress']

            # Draw particle with trail
            particle_alpha = int(self.laser_alpha * (1.0 - particle['progress'] * 0.5))
            particle_color = (*particle['color'], particle_alpha)

            # Main particle
            pygame.draw.circle(surface, particle_color,
                             (int(current_x), int(current_y)), 4)

            # Trail
            if particle['progress'] > 0.1:
                trail_progress = particle['progress'] - 0.1
                trail_x = particle['start_x'] + (particle['end_x'] - particle['start_x']) * trail_progress
                trail_y = particle['start_y'] + (particle['end_y'] - particle['start_y']) * trail_progress
                trail_alpha = int(particle_alpha * 0.5)
                pygame.draw.line(surface, (*particle['color'], trail_alpha),
                               (int(trail_x), int(trail_y)),
                               (int(current_x), int(current_y)), 2)

        # Draw scanning beams during scan phases
        if self.phase == "first_scan":
            # Horizontal and vertical sweeps - bright red lasers
            # Horizontal sweep
            sweep_y = self.center_y - self.grid_size * 1.5 + self.scan_progress * (self.grid_size * 3)
            pygame.draw.line(surface, laser_bright,
                           (self.center_x - self.grid_size * 1.5, sweep_y),
                           (self.center_x + self.grid_size * 1.5, sweep_y), 4)

            # Vertical sweep
            sweep_x = self.center_x - self.grid_size * 1.5 + self.scan_progress * (self.grid_size * 3)
            pygame.draw.line(surface, laser_bright,
                           (sweep_x, self.center_y - self.grid_size * 1.5),
                           (sweep_x, self.center_y + self.grid_size * 1.5), 4)

            # Intersection glow - yellow
            pygame.draw.circle(surface, (255, 255, 100, self.laser_alpha),
                             (int(sweep_x), int(sweep_y)), 8)

        elif self.phase == "second_scan":
            # Diagonal sweeps for second pass - yellow lasers
            # Diagonal 1 (top-left to bottom-right)
            diag_offset = (self.scan_progress - 0.5) * self.grid_size * 3
            start1_x = self.center_x - self.grid_size * 1.5 + diag_offset
            start1_y = self.center_y - self.grid_size * 1.5
            end1_x = self.center_x + self.grid_size * 1.5 + diag_offset
            end1_y = self.center_y + self.grid_size * 1.5
            pygame.draw.line(surface, laser_yellow,
                           (start1_x, start1_y), (end1_x, end1_y), 4)

            # Diagonal 2 (top-right to bottom-left)
            start2_x = self.center_x + self.grid_size * 1.5 - diag_offset
            start2_y = self.center_y - self.grid_size * 1.5
            end2_x = self.center_x - self.grid_size * 1.5 - diag_offset
            end2_y = self.center_y + self.grid_size * 1.5
            pygame.draw.line(surface, laser_yellow,
                           (start2_x, start2_y), (end2_x, end2_y), 4)

        # Draw tactical markers (appear during overlay phase) - green to match corner markers
        for marker in self.tactical_markers:
            if marker['alpha'] > 0:
                # Hexagonal marker with directional indicators
                size = marker['size']
                alpha = marker['alpha']

                # Outer hexagon - green
                hex_points = []
                for i in range(6):
                    angle = math.radians(60 * i)
                    px = marker['x'] + size * math.cos(angle)
                    py = marker['y'] + size * math.sin(angle)
                    hex_points.append((px, py))

                pygame.draw.polygon(surface, (0, 255, 0, alpha), hex_points, 2)

                # Inner crosshair - green
                cross_size = size * 0.5
                pygame.draw.line(surface, (0, 255, 0, alpha),
                               (marker['x'] - cross_size, marker['y']),
                               (marker['x'] + cross_size, marker['y']), 2)
                pygame.draw.line(surface, (0, 255, 0, alpha),
                               (marker['x'], marker['y'] - cross_size),
                               (marker['x'], marker['y'] + cross_size), 2)

        # Draw center reticle (always visible during active phases)
        if self.phase not in ["initialization", "complete"]:
            reticle_size = 15
            reticle_alpha = self.laser_alpha

            # Rotating outer ring
            rotation = self.timer * 180  # Degrees
            for i in range(4):
                angle = math.radians(rotation + i * 90)
                segment_start = angle
                segment_end = angle + math.radians(60)

                # Arc segment (approximated with lines)
                arc_points = []
                for step in range(10):
                    arc_angle = segment_start + (segment_end - segment_start) * step / 9
                    px = self.center_x + reticle_size * math.cos(arc_angle)
                    py = self.center_y + reticle_size * math.sin(arc_angle)
                    arc_points.append((int(px), int(py)))

                if len(arc_points) > 1:
                    pygame.draw.lines(surface, (255, 200, 0, reticle_alpha), False, arc_points, 3)

            # Center dot
            pygame.draw.circle(surface, (255, 255, 100, reticle_alpha),
                             (int(self.center_x), int(self.center_y)), 4)


class ExpediteRush:
    """EXPEDITE - MANDIBLE FOREMAN rushes forward in a line, stopping at first enemy."""
    def __init__(self, start_x, start_y, target_x, target_y, foreman_unit, target_grid_pos=None, camera=None):
        self.start_x = start_x
        self.start_y = start_y
        self.current_x = start_x
        self.current_y = start_y
        self.foreman = foreman_unit  # Reference to FOREMAN unit for animation
        self.phase = "charging"  # charging, rushing, impact, complete
        self.timer = 0
        self.active = True

        # Store camera reference and get tile size
        self.camera = camera
        if camera:
            self.tile_size = camera.tile_size
        else:
            self.tile_size = TILE_SIZE


        # IMPORTANT: Use the foreman's actual final grid position (from game logic)
        # Game logic has already executed and placed the foreman at the correct tile
        # (stopping before enemies, etc). Use THAT as our animation target.
        self.target_grid_x = foreman_unit.grid_x
        self.target_grid_y = foreman_unit.grid_y

        # Convert the actual final position to screen coordinates
        if camera:
            self.target_x, self.target_y = camera.grid_to_screen(self.target_grid_x, self.target_grid_y)
        else:
            # Fallback without camera
            from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
            self.target_x = GRID_OFFSET_X + self.target_grid_x * self.tile_size + self.tile_size // 2
            self.target_y = GRID_OFFSET_Y + self.target_grid_y * self.tile_size + self.tile_size // 2

        # Debug: Log initial state
        print(f"[ExpediteRush INIT] Foreman's ACTUAL final grid position from game logic: ({self.target_grid_x}, {self.target_grid_y})")
        print(f"[ExpediteRush INIT] Animation: start screen ({start_x}, {start_y}) -> final screen ({self.target_x}, {self.target_y})")

        # Calculate rush direction (normalize to unit vector)
        dx = self.target_x - start_x
        dy = self.target_y - start_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.direction_x = dx / dist
            self.direction_y = dy / dist
        else:
            self.direction_x = 1
            self.direction_y = 0

        # Rush speed (very fast)
        self.rush_speed = 800  # pixels per second

        # Trail positions for motion blur
        self.trail_positions = []

        # Target unit (enemy hit)
        self.target_unit = None
        self.damage_applied = False

        # Steam particles
        self.steam_particles = []

        play_sound("expedite_charge")

    def update(self, delta_time):
        """Update expedite rush animation."""
        self.timer += delta_time

        if self.phase == "charging":
            # Build up steam pressure (0.3s)
            if self.timer < 0.3:
                # Create charging steam particles
                if random.random() < 0.4:
                    # Steam venting from sides
                    side = random.choice([-1, 1])
                    angle = math.atan2(self.direction_y, self.direction_x) + side * math.pi/2
                    speed = random.uniform(30, 60)
                    particle = Particle(
                        self.current_x + side * 15,
                        self.current_y,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        (220, 220, 230), random.uniform(4, 8), 0.5
                    )
                    particle.gravity = -20  # Float upward
                    self.steam_particles.append(particle)
            else:
                self.phase = "rushing"
                self.timer = 0
                # Store FOREMAN's starting position for restoration later
                self.foreman_original_x = self.foreman.x
                self.foreman_original_y = self.foreman.y
                print(f"[ExpediteRush CHARGING->RUSHING] Starting rush from ({self.current_x}, {self.current_y})")
                play_sound("expedite_rush")

        elif self.phase == "rushing":
            # Rush forward at high speed
            # Move toward target
            self.current_x += self.direction_x * self.rush_speed * delta_time
            self.current_y += self.direction_y * self.rush_speed * delta_time

            # Update foreman visual position to follow the animation
            # This makes the sprite move during the rush
            self.foreman.x = self.current_x
            self.foreman.y = self.current_y

            # Store trail positions
            self.trail_positions.append((self.current_x, self.current_y, self.timer))
            if len(self.trail_positions) > 8:
                self.trail_positions.pop(0)

            # Create dense steam trail particles for rapid movement effect
            # Spawn multiple particles per frame to create a continuous trail
            for _ in range(3):
                # Backward-facing steam in opposite direction of travel
                back_angle = math.atan2(self.direction_y, self.direction_x) + math.pi
                # Add some spread for more natural look
                angle_variation = random.uniform(-0.3, 0.3)
                actual_angle = back_angle + angle_variation

                # Vary speed for dissipating effect
                speed = random.uniform(30, 100)

                # Spawn slightly behind current position
                spawn_offset = random.uniform(5, 15)
                spawn_x = self.current_x - self.direction_x * spawn_offset
                spawn_y = self.current_y - self.direction_y * spawn_offset

                # Create steam particle with varying properties
                particle = Particle(
                    spawn_x,
                    spawn_y,
                    math.cos(actual_angle) * speed,
                    math.sin(actual_angle) * speed,
                    (200, 200, 220),
                    random.uniform(8, 16),  # Larger, more visible particles
                    random.uniform(0.5, 0.8)  # Longer lifetime for visible trail
                )
                particle.gravity = random.uniform(20, 40)  # Vary gravity for spread
                self.steam_particles.append(particle)

            # Add occasional larger steam puffs for emphasis
            if random.random() < 0.3:
                back_angle = math.atan2(self.direction_y, self.direction_x) + math.pi
                puff_x = self.current_x - self.direction_x * 20
                puff_y = self.current_y - self.direction_y * 20
                puff = Particle(
                    puff_x, puff_y,
                    math.cos(back_angle) * 60,
                    math.sin(back_angle) * 60,
                    (220, 220, 240),
                    random.uniform(20, 30),  # Large puff
                    1.0  # Long-lasting
                )
                puff.gravity = 30
                self.steam_particles.append(puff)

            # Check if reached target (within threshold)
            dx_remaining = self.target_x - self.current_x
            dy_remaining = self.target_y - self.current_y
            dist_remaining = math.sqrt(dx_remaining*dx_remaining + dy_remaining*dy_remaining)

            if dist_remaining < self.rush_speed * delta_time * 1.5:
                # Reached target - transition to impact
                self.phase = "impact"
                self.timer = 0
                self.current_x = self.target_x
                self.current_y = self.target_y

                # Ensure foreman sprite is at exact target position
                self.foreman.x = self.target_x
                self.foreman.y = self.target_y

                print(f"[ExpediteRush RUSHING->IMPACT] Reached target screen ({self.target_x}, {self.target_y}), grid ({self.foreman.grid_x}, {self.foreman.grid_y})")
                play_sound("expedite_impact")

        elif self.phase == "impact":
            # Brief impact pause (0.2s)
            if self.timer >= 0.2:
                self.phase = "complete"
                self.timer = 0

        elif self.phase == "complete":
            # Fade out (0.3s) - sync FOREMAN visual position to grid position
            if self.timer >= 0.3:
                # CRITICAL FIX: Sync visual position (x, y) to match grid position (grid_x, grid_y)
                # During the animation, we modified screen coords directly which caused desync
                # Now force visual position to match the actual grid position
                if self.camera:
                    self.foreman.x, self.foreman.y = self.camera.grid_to_screen(self.foreman.grid_x, self.foreman.grid_y)
                else:
                    # Fallback without camera
                    from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
                    self.foreman.x = GRID_OFFSET_X + self.foreman.grid_x * self.tile_size + self.tile_size // 2
                    self.foreman.y = GRID_OFFSET_Y + self.foreman.grid_y * self.tile_size + self.tile_size // 2

                print(f"[ExpediteRush COMPLETE] Synced foreman visual position to grid ({self.foreman.grid_x}, {self.foreman.grid_y}) -> screen ({self.foreman.x}, {self.foreman.y})")
                self.active = False
                return False

        # Update steam particles
        self.steam_particles = [p for p in self.steam_particles if p.update(delta_time)]

        return True

    def draw(self, surface):
        """Draw the expedite rush animation."""
        if not self.active:
            return

        # Draw steam particles
        for particle in self.steam_particles:
            particle.draw(surface)

        if self.phase == "charging":
            # Draw charging indicator - pulsing glow around FOREMAN
            pulse = (math.sin(self.timer * 20) + 1) / 2
            glow_size = int(30 + pulse * 10)
            glow_alpha = int(100 + pulse * 50)

            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (220, 220, 255, glow_alpha),
                             (glow_size, glow_size), glow_size)
            glow_rect = glow_surf.get_rect(center=(int(self.current_x), int(self.current_y)))
            surface.blit(glow_surf, glow_rect)

            # Direction indicator (arrow pointing forward)
            arrow_length = 40
            arrow_end_x = self.current_x + self.direction_x * arrow_length
            arrow_end_y = self.current_y + self.direction_y * arrow_length
            pygame.draw.line(surface, (180, 180, 200, 200),
                           (int(self.current_x), int(self.current_y)),
                           (int(arrow_end_x), int(arrow_end_y)), 4)

        elif self.phase == "rushing":
            # Draw continuous dissipating steam trail along the path
            if len(self.trail_positions) > 1:
                # Draw thick steam trail connecting all path positions
                for i in range(len(self.trail_positions) - 1):
                    trail_x1, trail_y1, _ = self.trail_positions[i]
                    trail_x2, trail_y2, _ = self.trail_positions[i + 1]

                    # Calculate fade for this segment (older = more transparent)
                    segment_progress = i / max(len(self.trail_positions) - 1, 1)
                    alpha = int(200 * segment_progress)

                    # Draw thick steam line with soft edges
                    line_width = int(40 - segment_progress * 15)  # Thins out over time

                    # Draw multiple overlapping lines for soft steam effect
                    for layer in range(3):
                        layer_width = line_width - layer * 8
                        layer_alpha = alpha // (layer + 1)
                        if layer_width > 2:
                            pygame.draw.line(surface, (210, 210, 230, layer_alpha),
                                           (int(trail_x1), int(trail_y1)),
                                           (int(trail_x2), int(trail_y2)),
                                           layer_width)

            # Also draw steam clouds at each position for extra density
            for i, (trail_x, trail_y, trail_time) in enumerate(self.trail_positions):
                trail_progress = i / max(len(self.trail_positions), 1)
                alpha = int(150 * trail_progress)
                cloud_size = int(30 * (1 - trail_progress * 0.3))

                # Draw soft steam cloud
                steam_surf = pygame.Surface((cloud_size * 2, cloud_size * 2), pygame.SRCALPHA)
                for j in range(2):
                    offset = j * 6
                    size = cloud_size - offset
                    cloud_alpha = alpha // (j + 1)
                    if size > 0:
                        pygame.draw.circle(steam_surf, (210, 210, 230, cloud_alpha),
                                         (cloud_size, cloud_size), size)

                trail_rect = steam_surf.get_rect(center=(int(trail_x), int(trail_y)))
                surface.blit(steam_surf, trail_rect)

            # Draw FOREMAN's rushing silhouette with glow
            rush_glow = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(rush_glow, (220, 230, 255, 200), (25, 25), 25)
            rush_rect = rush_glow.get_rect(center=(int(self.current_x), int(self.current_y)))
            surface.blit(rush_glow, rush_rect)

            # Speed lines indicating direction
            for i in range(3):
                line_offset = (i - 1) * 15
                perp_x = -self.direction_y * line_offset
                perp_y = self.direction_x * line_offset
                line_start_x = self.current_x + perp_x - self.direction_x * 30
                line_start_y = self.current_y + perp_y - self.direction_y * 30
                line_end_x = self.current_x + perp_x
                line_end_y = self.current_y + perp_y
                pygame.draw.line(surface, (180, 190, 200, 150),
                               (int(line_start_x), int(line_start_y)),
                               (int(line_end_x), int(line_end_y)), 3)

        elif self.phase == "impact":
            # Draw impact burst
            impact_progress = self.timer / 0.2
            burst_size = int(40 + impact_progress * 60)
            burst_alpha = int(255 * (1 - impact_progress))

            # White impact flash
            burst_surf = pygame.Surface((burst_size * 2, burst_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(burst_surf, (255, 255, 255, burst_alpha),
                             (burst_size, burst_size), burst_size)
            burst_rect = burst_surf.get_rect(center=(int(self.current_x), int(self.current_y)))
            surface.blit(burst_surf, burst_rect)

            # Shockwave ring
            ring_radius = int(burst_size * 0.7)
            pygame.draw.circle(surface, (220, 220, 240, burst_alpha),
                             (int(self.current_x), int(self.current_y)), ring_radius, 4)


class JawlineNetwork:
    """JAWLINE - Network of mechanical bear trap jaws deployed in 3x3 grid around MANDIBLE FOREMAN."""
    def __init__(self, center_x, center_y, camera=None):
        self.center_x = center_x
        self.center_y = center_y
        self.phase = "deploying"  # deploying, snapping, active, fading
        self.timer = 0
        self.active = True
        self.damage_targets = []  # Units that will take damage
        self.damage_applied = False

        # Get tile size from camera (or fallback to default)
        if camera:
            self.tile_size = camera.tile_size
        else:
            self.tile_size = TILE_SIZE

        # 8 trap positions in 3x3 grid (excluding center where FOREMAN stands)
        self.trap_positions = []
        trap_index = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip center
                trap_x = center_x + dx * self.tile_size
                trap_y = center_y + dy * self.tile_size
                self.trap_positions.append({
                    'x': trap_x,
                    'y': trap_y,
                    'dx': dx,
                    'dy': dy,
                    'deploy_progress': 0,
                    'jaw_angle': 45,  # Bear trap jaw opening angle (degrees)
                    'cable_slack': 0,
                    'deploy_delay': trap_index * 0.06  # Stagger deployment
                })
                trap_index += 1

        play_sound("jawline_deploy")

    def update(self, delta_time):
        """Update jawline network animation."""
        self.timer += delta_time

        if self.phase == "deploying":
            # Traps slide out from center along cables
            all_deployed = True
            for trap in self.trap_positions:
                if self.timer >= trap['deploy_delay']:
                    deploy_time = self.timer - trap['deploy_delay']
                    if deploy_time < 0.35:
                        trap['deploy_progress'] = deploy_time / 0.35
                        # Cable slack diminishes as trap deploys
                        trap['cable_slack'] = (1.0 - trap['deploy_progress']) * 0.25
                        all_deployed = False  # Still deploying
                    else:
                        trap['deploy_progress'] = 1.0
                        trap['cable_slack'] = 0
                else:
                    all_deployed = False  # Hasn't started yet

            # Only transition when ALL traps have fully deployed (deploy_progress = 1.0)
            if all_deployed:
                self.phase = "snapping"
                self.timer = 0
                play_sound("jawline_snap")

        elif self.phase == "snapping":
            # All traps snap shut simultaneously (0.12s fast snap)
            if self.timer < 0.12:
                snap_progress = self.timer / 0.12
                for trap in self.trap_positions:
                    # Jaws close from 45° to 0° with ease-in
                    ease = snap_progress * snap_progress
                    trap['jaw_angle'] = 45 * (1.0 - ease)
            else:
                for trap in self.trap_positions:
                    trap['jaw_angle'] = 0
                self.phase = "active"
                self.timer = 0
                # Damage applied when jaws snap shut
                self.damage_applied = True

        elif self.phase == "active":
            # Hold active state with pulsing glow (1.5s)
            if self.timer >= 1.5:
                self.phase = "fading"
                self.timer = 0

        elif self.phase == "fading":
            # Fade out (0.3s)
            if self.timer >= 0.3:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the jawline network."""
        if not self.active:
            return

        # Calculate alpha for fading
        if self.phase == "fading":
            alpha = int(255 * (1.0 - self.timer / 0.3))
        else:
            alpha = 255

        # Pulsing glow during active phase
        pulse_intensity = 1.0
        if self.phase == "active":
            pulse = (math.sin(self.timer * 10) + 1) / 2  # Fast pulse
            pulse_intensity = 0.6 + pulse * 0.4

        # Orange cable color (matching FOREMAN's SVG)
        cable_base_alpha = int(alpha * pulse_intensity)
        cable_color = (255, 102, 0, cable_base_alpha)  # #ff6600

        # Draw orange cables connecting traps to center
        for trap in self.trap_positions:
            if trap['deploy_progress'] > 0:
                # Calculate current trap position (lerp from center to final position)
                current_x = self.center_x + (trap['x'] - self.center_x) * trap['deploy_progress']
                current_y = self.center_y + (trap['y'] - self.center_y) * trap['deploy_progress']

                # Draw cable with curve for slack
                if trap['cable_slack'] > 0:
                    # Quadratic Bezier curve for cable slack
                    mid_x = (self.center_x + current_x) / 2
                    mid_y = (self.center_y + current_y) / 2
                    # Perpendicular offset for slack
                    dx = current_x - self.center_x
                    dy = current_y - self.center_y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        perp_x = -dy / dist * trap['cable_slack'] * self.tile_size * 0.5
                        perp_y = dx / dist * trap['cable_slack'] * self.tile_size * 0.5
                    else:
                        perp_x = perp_y = 0
                    control_x = mid_x + perp_x
                    control_y = mid_y + perp_y

                    # Draw curve as line segments
                    points = []
                    for t_step in range(11):
                        t = t_step / 10
                        # Quadratic Bezier: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
                        bx = (1-t)**2 * self.center_x + 2*(1-t)*t * control_x + t**2 * current_x
                        by = (1-t)**2 * self.center_y + 2*(1-t)*t * control_y + t**2 * current_y
                        points.append((int(bx), int(by)))

                    if len(points) > 1:
                        pygame.draw.lines(surface, cable_color, False, points, 3)
                else:
                    # Straight taut cable
                    pygame.draw.line(surface, cable_color,
                                   (int(self.center_x), int(self.center_y)),
                                   (int(current_x), int(current_y)), 3)

        # Draw bear trap jaws at each position
        for trap in self.trap_positions:
            if trap['deploy_progress'] > 0:
                current_x = self.center_x + (trap['x'] - self.center_x) * trap['deploy_progress']
                current_y = self.center_y + (trap['y'] - self.center_y) * trap['deploy_progress']
                trap_alpha = int(alpha * pulse_intensity)
                self.draw_bear_trap(surface, current_x, current_y, trap['jaw_angle'], trap_alpha)

        # Draw central hub (cable spool on FOREMAN's position)
        hub_radius = 10
        pygame.draw.circle(surface, (120, 120, 130, alpha),
                         (int(self.center_x), int(self.center_y)), hub_radius)
        pygame.draw.circle(surface, (80, 80, 90, alpha),
                         (int(self.center_x), int(self.center_y)), hub_radius, 3)
        # Orange pulsing indicator light on hub
        if self.phase in ["active", "snapping"]:
            light_size = int(4 + pulse_intensity * 2)
            light_alpha = int(alpha * pulse_intensity)
            pygame.draw.circle(surface, (255, 150, 0, light_alpha),
                             (int(self.center_x), int(self.center_y)), light_size)

    def draw_bear_trap(self, surface, x, y, jaw_angle, alpha):
        """Draw a mechanical bear trap with adjustable jaw angle."""
        trap_size = 24

        # Create surface for the trap
        trap_surf = pygame.Surface((trap_size * 3, trap_size * 3), pygame.SRCALPHA)
        center = trap_size * 1.5

        # Metal colors
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        metal_teeth = (200, 200, 210, alpha)

        # Base plate
        base_w = int(trap_size * 0.8)
        base_h = int(trap_size * 0.4)
        base_rect = pygame.Rect(center - base_w // 2, center - base_h // 2, base_w, base_h)
        pygame.draw.rect(trap_surf, metal_dark, base_rect)
        pygame.draw.rect(trap_surf, metal_light, base_rect, 2)

        # Central hinge pivot
        pygame.draw.circle(trap_surf, metal_light, (int(center), int(center)), 5)
        pygame.draw.circle(trap_surf, metal_dark, (int(center), int(center)), 5, 2)

        # Draw upper and lower jaws
        self.draw_trap_jaw(trap_surf, center, center, jaw_angle, True, alpha)  # Upper jaw
        self.draw_trap_jaw(trap_surf, center, center, jaw_angle, False, alpha)  # Lower jaw

        # Blit to main surface
        trap_rect = trap_surf.get_rect(center=(int(x), int(y)))
        surface.blit(trap_surf, trap_rect)

    def draw_trap_jaw(self, surface, cx, cy, angle, is_upper, alpha):
        """Draw a single jaw of the bear trap."""
        # Metal colors
        metal_light = (160, 160, 170, alpha)
        metal_teeth = (200, 200, 210, alpha)
        metal_dark = (100, 100, 110, alpha)

        # Jaw parameters
        jaw_length = 20
        jaw_width = 9

        # Calculate jaw angle (upper jaw rotates up, lower rotates down)
        angle_rad = math.radians(angle if is_upper else -angle)

        # Jaw arm as quadrilateral
        arm_points = []
        # Near points at hinge
        for side_offset in [-jaw_width//2, jaw_width//2]:
            px = cx + side_offset * math.cos(angle_rad + math.pi/2)
            py = cy + side_offset * math.sin(angle_rad + math.pi/2)
            arm_points.append((px, py))
        # Far points at end
        for side_offset in [jaw_width//2, -jaw_width//2]:
            px = cx + jaw_length * math.cos(angle_rad) + side_offset * math.cos(angle_rad + math.pi/2)
            py = cy + jaw_length * math.sin(angle_rad) + side_offset * math.sin(angle_rad + math.pi/2)
            arm_points.append((px, py))

        pygame.draw.polygon(surface, metal_light, arm_points)
        pygame.draw.polygon(surface, metal_dark, arm_points, 2)

        # Teeth along the jaw (4 sharp teeth pointing inward)
        for tooth_idx in range(4):
            tooth_dist = (tooth_idx + 0.7) * jaw_length / 4.5
            tooth_base_x = cx + tooth_dist * math.cos(angle_rad)
            tooth_base_y = cy + tooth_dist * math.sin(angle_rad)

            # Tooth length and direction (perpendicular, pointing inward)
            tooth_length = 6
            tooth_angle = angle_rad + (math.pi/2 if not is_upper else -math.pi/2)

            # Triangle tooth
            tooth_tip_x = tooth_base_x + tooth_length * math.cos(tooth_angle)
            tooth_tip_y = tooth_base_y + tooth_length * math.sin(tooth_angle)

            tooth_base_offset = 2.5
            tooth_base1_x = tooth_base_x + tooth_base_offset * math.cos(angle_rad)
            tooth_base1_y = tooth_base_y + tooth_base_offset * math.sin(angle_rad)
            tooth_base2_x = tooth_base_x - tooth_base_offset * math.cos(angle_rad)
            tooth_base2_y = tooth_base_y - tooth_base_offset * math.sin(angle_rad)

            tooth_points = [
                (tooth_tip_x, tooth_tip_y),
                (tooth_base1_x, tooth_base1_y),
                (tooth_base2_x, tooth_base2_y)
            ]
            pygame.draw.polygon(surface, metal_teeth, tooth_points)
            pygame.draw.polygon(surface, metal_light, tooth_points, 1)


class JawlineNetworkUpgraded:
    """
    UPGRADED JAWLINE - Directional cable spools roll out in chosen direction.
    Foreman releases 3 cable spools that roll forward, unspooling cables with bear traps.
    """
    def __init__(self, center_x, center_y, target_x, target_y, camera=None, game=None, caster_unit=None):
        self.center_x = center_x
        self.center_y = center_y
        self.target_x = target_x
        self.target_y = target_y
        self.phase = "launch"  # launch, rolling, deploying_traps, snapping, active, fading
        self.timer = 0
        self.active = True
        self.camera = camera
        self.game = game
        self.caster_unit = caster_unit

        # Get tile size from camera
        if camera:
            self.tile_size = camera.tile_size
        else:
            self.tile_size = TILE_SIZE

        # Convert screen positions to grid positions to get proper direction
        if camera:
            from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
            caster_grid_x = (center_x - GRID_OFFSET_X) // self.tile_size
            caster_grid_y = (center_y - GRID_OFFSET_Y) // self.tile_size
            target_grid_x = (target_x - GRID_OFFSET_X) // self.tile_size
            target_grid_y = (target_y - GRID_OFFSET_Y) // self.tile_size
        else:
            # Fallback without camera
            caster_grid_x = center_x // self.tile_size
            caster_grid_y = center_y // self.tile_size
            target_grid_x = target_x // self.tile_size
            target_grid_y = target_y // self.tile_size

        # Calculate grid direction (unit vector in grid space)
        grid_dx = target_grid_x - caster_grid_x
        grid_dy = target_grid_y - caster_grid_y

        # Normalize to unit direction (-1, 0, or 1 for each component)
        if grid_dy != 0:
            self.dir_grid_y = grid_dy // abs(grid_dy)
        else:
            self.dir_grid_y = 0

        if grid_dx != 0:
            self.dir_grid_x = grid_dx // abs(grid_dx)
        else:
            self.dir_grid_x = 0

        # Calculate perpendicular direction in grid space for the 3-wide part
        if self.dir_grid_y == 0:  # Horizontal line
            self.perp_grid_y, self.perp_grid_x = 1, 0
        elif self.dir_grid_x == 0:  # Vertical line
            self.perp_grid_y, self.perp_grid_x = 0, 1
        else:  # Diagonal line
            self.perp_grid_y, self.perp_grid_x = -self.dir_grid_x, self.dir_grid_y

        # Store caster grid position for calculations
        self.caster_grid_x = caster_grid_x
        self.caster_grid_y = caster_grid_y

        # Three rolling cable spools (center, left, right) - positioned on grid
        self.spools = []
        for offset in [-1, 0, 1]:  # Left, center, right
            # Calculate starting grid position for this lane
            start_grid_x = caster_grid_x + self.perp_grid_x * offset
            start_grid_y = caster_grid_y + self.perp_grid_y * offset

            # Convert to screen coordinates (center of tile)
            if camera:
                spool_x = GRID_OFFSET_X + start_grid_x * self.tile_size + self.tile_size // 2
                spool_y = GRID_OFFSET_Y + start_grid_y * self.tile_size + self.tile_size // 2
            else:
                spool_x = start_grid_x * self.tile_size + self.tile_size // 2
                spool_y = start_grid_y * self.tile_size + self.tile_size // 2

            self.spools.append({
                'start_x': spool_x,
                'start_y': spool_y,
                'x': spool_x,
                'y': spool_y,
                'start_grid_x': start_grid_x,
                'start_grid_y': start_grid_y,
                'offset': offset,  # -1, 0, 1
                'rotation': 0,  # Rotation angle for rolling
                'tiles_traveled': 0,  # Number of tiles traveled
                'traps_deployed': [],  # Trap positions along this spool's path
                'blocked': False  # Whether this lane is blocked
            })

        # Track deployed traps across all spools
        self.all_traps = []

        # Rolling speed (tiles per second)
        self.roll_speed = 6  # 6 tiles per second

        # Maximum roll distance (9 tiles)
        self.max_tiles = 9

        play_sound("jawline_upgraded_launch")

    def update(self, delta_time):
        """Update upgraded jawline animation."""
        self.timer += delta_time

        if self.phase == "launch":
            # Brief launch preparation (0.2s)
            if self.timer >= 0.2:
                self.phase = "rolling"
                self.timer = 0
                play_sound("jawline_upgraded_roll")

        elif self.phase == "rolling":
            # Spools roll forward tile-by-tile, deploying cable and traps
            # Calculate how many tiles we should have traveled
            tiles_should_travel = self.roll_speed * self.timer

            for spool in self.spools:
                if spool['blocked']:
                    continue

                # Calculate target tile for this spool
                target_tiles = min(int(tiles_should_travel), self.max_tiles)

                if target_tiles > spool['tiles_traveled']:
                    # Deploy trap at the new tile
                    new_tile_distance = target_tiles

                    # Calculate grid position of new trap
                    trap_grid_x = spool['start_grid_x'] + self.dir_grid_x * new_tile_distance
                    trap_grid_y = spool['start_grid_y'] + self.dir_grid_y * new_tile_distance

                    # Check if this position is blocked (terrain, furniture, or enemy unit)
                    is_blocked = False
                    if self.game:
                        # Check if position is valid
                        if not self.game.is_valid_position(trap_grid_y, trap_grid_x):
                            is_blocked = True
                        # Check if blocked by impassable terrain
                        elif not self.game.map.is_passable(trap_grid_y, trap_grid_x):
                            is_blocked = True
                        # Check if blocked by furniture (line of sight check from previous tile)
                        elif new_tile_distance > 1:
                            prev_grid_x = spool['start_grid_x'] + self.dir_grid_x * (new_tile_distance - 1)
                            prev_grid_y = spool['start_grid_y'] + self.dir_grid_y * (new_tile_distance - 1)
                            if not self.game.has_line_of_sight(prev_grid_y, prev_grid_x, trap_grid_y, trap_grid_x):
                                is_blocked = True
                        else:
                            # For first tile, check from caster
                            if not self.game.has_line_of_sight(self.caster_grid_y, self.caster_grid_x, trap_grid_y, trap_grid_x):
                                is_blocked = True

                    # If blocked by terrain/furniture, stop this spool
                    if is_blocked:
                        spool['blocked'] = True
                        spool['tiles_traveled'] = new_tile_distance - 1  # Stop at previous tile
                        continue

                    # Note: Enemy units do NOT block - spools pass through them

                    # Convert to screen coordinates (center of tile)
                    if self.camera:
                        from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
                        trap_x = GRID_OFFSET_X + trap_grid_x * self.tile_size + self.tile_size // 2
                        trap_y = GRID_OFFSET_Y + trap_grid_y * self.tile_size + self.tile_size // 2
                    else:
                        trap_x = trap_grid_x * self.tile_size + self.tile_size // 2
                        trap_y = trap_grid_y * self.tile_size + self.tile_size // 2

                    # Create trap at this position
                    trap_data = {
                        'x': trap_x,
                        'y': trap_y,
                        'grid_x': trap_grid_x,
                        'grid_y': trap_grid_y,
                        'jaw_angle': 45,  # Start open
                        'deploy_time': self.timer,
                        'spool': spool
                    }
                    spool['traps_deployed'].append(trap_data)
                    self.all_traps.append(trap_data)
                    spool['tiles_traveled'] = target_tiles

                # Update spool position (smooth interpolation between tiles)
                if not spool['blocked']:
                    progress_to_next_tile = tiles_should_travel - spool['tiles_traveled']
                    if progress_to_next_tile > 0 and spool['tiles_traveled'] < self.max_tiles:
                        # Spool is between tiles - interpolate position
                        current_tile_distance = spool['tiles_traveled'] + progress_to_next_tile
                    else:
                        current_tile_distance = spool['tiles_traveled']
                else:
                    # Blocked - stay at final position
                    current_tile_distance = spool['tiles_traveled']

                # Calculate spool screen position
                spool_grid_x = spool['start_grid_x'] + self.dir_grid_x * current_tile_distance
                spool_grid_y = spool['start_grid_y'] + self.dir_grid_y * current_tile_distance

                if self.camera:
                    from boneglaive.graphical.renderer import GRID_OFFSET_X, GRID_OFFSET_Y
                    spool['x'] = GRID_OFFSET_X + spool_grid_x * self.tile_size + self.tile_size // 2
                    spool['y'] = GRID_OFFSET_Y + spool_grid_y * self.tile_size + self.tile_size // 2
                else:
                    spool['x'] = spool_grid_x * self.tile_size + self.tile_size // 2
                    spool['y'] = spool_grid_y * self.tile_size + self.tile_size // 2

                # Update rotation (rolls as it moves)
                spool['rotation'] = (current_tile_distance * 360)  # Full rotation per tile

                # Check if reached max distance
                if spool['tiles_traveled'] >= self.max_tiles:
                    spool['blocked'] = True

            # Check if all spools are blocked or at max distance
            if all(spool['blocked'] for spool in self.spools):
                self.phase = "deploying_traps"
                self.timer = 0
                play_sound("jawline_upgraded_deploy")

        elif self.phase == "deploying_traps":
            # Brief pause to show all traps deployed (0.15s)
            if self.timer >= 0.15:
                self.phase = "snapping"
                self.timer = 0
                play_sound("jawline_upgraded_snap")

        elif self.phase == "snapping":
            # All traps snap shut simultaneously (0.12s)
            if self.timer < 0.12:
                snap_progress = self.timer / 0.12
                for trap in self.all_traps:
                    # Jaws close from 45° to 0° with ease-in
                    ease = snap_progress * snap_progress
                    trap['jaw_angle'] = 45 * (1.0 - ease)
            else:
                for trap in self.all_traps:
                    trap['jaw_angle'] = 0
                self.phase = "active"
                self.timer = 0

        elif self.phase == "active":
            # Hold active state (0.8s)
            if self.timer >= 0.8:
                self.phase = "fading"
                self.timer = 0

        elif self.phase == "fading":
            # Fade out (0.3s)
            if self.timer >= 0.3:
                self.active = False
                return False

        return True

    def draw(self, surface):
        """Draw the upgraded jawline animation."""
        if not self.active:
            return

        # Calculate alpha for fading
        if self.phase == "fading":
            alpha = int(255 * (1.0 - self.timer / 0.3))
        else:
            alpha = 255

        # Orange cable color
        cable_color = (255, 102, 0, alpha)

        # Draw cables from FOREMAN to each spool
        for spool in self.spools:
            if spool['tiles_traveled'] > 0:
                # Draw cable as line from start to current spool position
                pygame.draw.line(surface, cable_color,
                               (int(spool['start_x']), int(spool['start_y'])),
                               (int(spool['x']), int(spool['y'])), 3)

        # Draw deployed traps
        for trap in self.all_traps:
            self.draw_bear_trap(surface, trap['x'], trap['y'], trap['jaw_angle'], alpha)

        # Draw rolling cable spools
        for spool in self.spools:
            if not spool['blocked'] or self.phase in ["snapping", "active", "fading"]:
                # Draw as rolling spool
                self.draw_cable_spool(surface, spool['x'], spool['y'], spool['rotation'], alpha)

    def draw_cable_spool(self, surface, x, y, rotation, alpha):
        """Draw a rolling cable spool."""
        spool_radius = 12

        # Create surface for the spool
        spool_surf = pygame.Surface((spool_radius * 4, spool_radius * 4), pygame.SRCALPHA)
        center = spool_radius * 2

        # Metal colors
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        orange = (255, 102, 0, alpha)

        # Outer rim
        pygame.draw.circle(spool_surf, metal_dark, (center, center), spool_radius)
        pygame.draw.circle(spool_surf, metal_light, (center, center), spool_radius, 2)

        # Draw cable wrapped around spool (rotating lines)
        num_spokes = 6
        for i in range(num_spokes):
            angle = math.radians(rotation + i * (360 / num_spokes))
            start_x = center + math.cos(angle) * (spool_radius * 0.3)
            start_y = center + math.sin(angle) * (spool_radius * 0.3)
            end_x = center + math.cos(angle) * spool_radius
            end_y = center + math.sin(angle) * spool_radius
            pygame.draw.line(spool_surf, orange, (start_x, start_y), (end_x, end_y), 2)

        # Center hub
        pygame.draw.circle(spool_surf, metal_light, (center, center), int(spool_radius * 0.4))
        pygame.draw.circle(spool_surf, metal_dark, (center, center), int(spool_radius * 0.4), 1)

        # Blit to main surface
        spool_rect = spool_surf.get_rect(center=(int(x), int(y)))
        surface.blit(spool_surf, spool_rect)

    def draw_bear_trap(self, surface, x, y, jaw_angle, alpha):
        """Draw a mechanical bear trap (reusing base Jawline method)."""
        trap_size = 24

        # Create surface for the trap
        trap_surf = pygame.Surface((trap_size * 3, trap_size * 3), pygame.SRCALPHA)
        center = trap_size * 1.5

        # Metal colors
        metal_dark = (100, 100, 110, alpha)
        metal_light = (160, 160, 170, alpha)
        metal_teeth = (200, 200, 210, alpha)

        # Base plate
        base_w = int(trap_size * 0.8)
        base_h = int(trap_size * 0.4)
        base_rect = pygame.Rect(center - base_w // 2, center - base_h // 2, base_w, base_h)
        pygame.draw.rect(trap_surf, metal_dark, base_rect)
        pygame.draw.rect(trap_surf, metal_light, base_rect, 2)

        # Central hinge pivot
        pygame.draw.circle(trap_surf, metal_light, (int(center), int(center)), 5)
        pygame.draw.circle(trap_surf, metal_dark, (int(center), int(center)), 5, 2)

        # Draw upper and lower jaws
        self.draw_trap_jaw(trap_surf, center, center, jaw_angle, True, alpha)
        self.draw_trap_jaw(trap_surf, center, center, jaw_angle, False, alpha)

        # Blit to main surface
        trap_rect = trap_surf.get_rect(center=(int(x), int(y)))
        surface.blit(trap_surf, trap_rect)

    def draw_trap_jaw(self, surface, cx, cy, angle, is_upper, alpha):
        """Draw a single jaw of the bear trap."""
        # Metal colors
        metal_light = (160, 160, 170, alpha)
        metal_teeth = (200, 200, 210, alpha)
        metal_dark = (100, 100, 110, alpha)

        # Jaw parameters
        jaw_length = 20
        jaw_width = 9

        # Calculate jaw angle (upper jaw rotates up, lower rotates down)
        angle_rad = math.radians(angle if is_upper else -angle)

        # Jaw arm as quadrilateral
        arm_points = []
        # Near points at hinge
        for side_offset in [-jaw_width//2, jaw_width//2]:
            px = cx + side_offset * math.cos(angle_rad + math.pi/2)
            py = cy + side_offset * math.sin(angle_rad + math.pi/2)
            arm_points.append((px, py))
        # Far points at end
        for side_offset in [jaw_width//2, -jaw_width//2]:
            px = cx + jaw_length * math.cos(angle_rad) + side_offset * math.cos(angle_rad + math.pi/2)
            py = cy + jaw_length * math.sin(angle_rad) + side_offset * math.sin(angle_rad + math.pi/2)
            arm_points.append((px, py))

        pygame.draw.polygon(surface, metal_light, arm_points)
        pygame.draw.polygon(surface, metal_dark, arm_points, 2)

        # Teeth along the jaw (4 sharp teeth pointing inward)
        for tooth_idx in range(4):
            tooth_dist = (tooth_idx + 0.7) * jaw_length / 4.5
            tooth_base_x = cx + tooth_dist * math.cos(angle_rad)
            tooth_base_y = cy + tooth_dist * math.sin(angle_rad)

            # Tooth length and direction (perpendicular, pointing inward)
            tooth_length = 6
            tooth_angle = angle_rad + (math.pi/2 if not is_upper else -math.pi/2)

            # Triangle tooth
            tooth_tip_x = tooth_base_x + tooth_length * math.cos(tooth_angle)
            tooth_tip_y = tooth_base_y + tooth_length * math.sin(tooth_angle)

            tooth_base_offset = 2.5
            tooth_base1_x = tooth_base_x + tooth_base_offset * math.cos(angle_rad)
            tooth_base1_y = tooth_base_y + tooth_base_offset * math.sin(angle_rad)
            tooth_base2_x = tooth_base_x - tooth_base_offset * math.cos(angle_rad)
            tooth_base2_y = tooth_base_y - tooth_base_offset * math.sin(angle_rad)

            tooth_points = [
                (tooth_tip_x, tooth_tip_y),
                (tooth_base1_x, tooth_base1_y),
                (tooth_base2_x, tooth_base2_y)
            ]
            pygame.draw.polygon(surface, metal_teeth, tooth_points)
            pygame.draw.polygon(surface, metal_light, tooth_points, 1)


