#!/usr/bin/env python3
"""
MANDIBLE FOREMAN Animation Classes
Skill animations for the MANDIBLE FOREMAN unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, COLOR_DAMAGE, Particle

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

        elif self.phase == "impact":
            # Brief impact pause (0.2s)
            if self.timer >= 0.2:
                self.phase = "complete"
                self.timer = 0

        elif self.phase == "complete":
            # Fade out (0.3s) - keep FOREMAN at new position
            if self.timer >= 0.3:
                # Don't restore position - FOREMAN stays where he rushed to
                # Position will be reset at end of full skill rotation
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


