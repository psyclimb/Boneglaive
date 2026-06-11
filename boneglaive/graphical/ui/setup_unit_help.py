#!/usr/bin/env python3
"""
Setup Unit Help Panel
Side panel showing detailed unit information during setup phase.
"""
import pygame
from typing import Optional, Tuple
from pathlib import Path
import sys
from boneglaive.utils.paths import asset_path, load_svg

# Import unit types and skills
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from boneglaive.utils.constants import UnitType, UNIT_STATS
from .scrollbar import Scrollbar

# Colors
COLOR_BG = (30, 34, 42)
COLOR_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_GOLD = (255, 215, 0)
COLOR_SECTION = (50, 54, 62)


class SetupUnitHelp:
    """Help panel showing unit details during setup."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.unit_type = None
        self.scroll_offset = 0
        self.max_scroll = 0
        self.content_surface = None
        self.has_focus = False

        # Calculate line spacing based on font size (scales with resolution)
        # Base spacing at 1280x720: small_font is ~16px, line spacing is 16-20px
        base_small_font_height = 16
        actual_small_font_height = small_font.get_height()
        self.spacing_scale = actual_small_font_height / base_small_font_height

        # Scrollbar component
        self.scrollbar = Scrollbar()

        # Unit display names - base units
        self.unit_names = {
            UnitType.GLAIVEMAN: "GLAIVEMAN",
            UnitType.MANDIBLE_FOREMAN: "MANDIBLE FOREMAN",
            UnitType.GRAYMAN: "GRAYMAN",
            UnitType.MARROW_CONDENSER: "MARROW CONDENSER",
            UnitType.FOWL_CONTRIVANCE: "FOWL CONTRIVANCE",
            UnitType.GAS_MACHINIST: "GAS MACHINIST",
            UnitType.DELPHIC_APPRAISER: "DELPHIC APPRAISER",
            UnitType.INTERFERER: "INTERFERER",
            UnitType.DERELICTIONIST: "DERELICTIONIST",
            UnitType.POTPOURRIST: "POTPOURRIST",
        }

        # Sprite cache
        self.sprite_cache = {}

        # Skill icon cache
        self.skill_icon_cache = {}

        # Load unit help data from ASCII help component
        self.unit_help_data = self._load_unit_help_data()

        # Load simplified unit info for setup phase
        self.simplified_info = self._load_simplified_info()

        # Toggle between simplified and advanced view
        self.show_advanced = False

    def _scale_spacing(self, base_pixels):
        """Scale a spacing value based on font size."""
        return int(base_pixels * self.spacing_scale)

    def _get_unit_name(self, unit_type):
        """Get display name for a unit type."""
        if isinstance(unit_type, str):
            return unit_type
        try:
            return unit_type.name
        except AttributeError:
            return str(unit_type)

    def _load_unit_help_data(self):
        """Load unit help data."""
        from boneglaive.game.unit_help_data import get_unit_help_data
        return get_unit_help_data()

    def _load_simplified_info(self):
        """Load simplified unit info for setup phase - brief descriptions only."""
        simplified_info = {
            UnitType.GLAIVEMAN: {
                'difficulty': 2,  # Out of 5
                'role': 'Frontline Fighter / Displacer',
                'overview': 'A versatile melee warrior wielding a polearm and sacred spinning glaives. This balanced frontline fighter excels at mobility and devastating retaliatory strikes.',
                'passive': {
                    'name': 'AUTOCLAVE',
                    'desc': 'When brought to critical health, unleashes a devastating cross-shaped retaliation that heals. Can only trigger once per life.'
                },
                'skills': [
                    {
                        'name': 'PRY',
                        'desc': 'Pries an adjacent enemy into the ceiling, reducing their movement. Nearby enemies take splash damage from falling debris.'
                    },
                    {
                        'name': 'VAULT',
                        'desc': 'Performs an athletic leap over obstacles and units to reposition freely.'
                    },
                    {
                        'name': 'JUDGEMENT',
                        'desc': 'Hurls a sacred spinning glaive that pierces enemy defenses and deals increased damage to critically wounded enemies.'
                    }
                ]
            },
            UnitType.MANDIBLE_FOREMAN: {
                'difficulty': 2,  # Out of 5
                'role': 'Frontline Fighter / Disabler',
                'overview': 'A mechanical supervisor wielding industrial jaw contraptions for area control and battlefield management. This durable frontline unit excels at trapping and immobilizing enemies while providing tactical support to allies.',
                'passive': {
                    'name': 'VISEROY',
                    'desc': 'Every basic attack automatically traps the target in hydraulic mechanical jaws that crush incrementally. Trapped enemies cannot move or use skills as the jaws tighten each turn.'
                },
                'skills': [
                    {
                        'name': 'EXPEDITE',
                        'desc': 'Rushes forward in a straight line, stopping at the first enemy encountered. The collision deals damage and immediately clamps the target in jaws.'
                    },
                    {
                        'name': 'SITE INSPECTION',
                        'desc': 'Conducts a tactical survey of an area, granting allies attack and movement bonuses based on terrain clarity. The inspection also reveals hidden traps.'
                    },
                    {
                        'name': 'JAWLINE',
                        'desc': 'Deploys a network of mechanical jaws across all adjacent tiles, dealing damage and completely disabling movement for trapped enemies.'
                    }
                ]
            },
            UnitType.GRAYMAN: {
                'difficulty': 1,  # Out of 5
                'role': 'Escape Artist / Disabler / Summoner',
                'overview': 'A gray alien-human hybrid occupying an unchangeable state, immune to all external manipulation. This ranged specialist teleports freely, weakens key targets, and creates doppelgangers that explode when destroyed.',
                'passive': {
                    'name': 'STASIALITY',
                    'desc': 'Occupies an unchangeable state, granting immunity to all status effects, stat modifications, forced movement, and terrain effects.'
                },
                'skills': [
                    {
                        'name': 'DELTA CONFIG',
                        'desc': 'Teleports to any unoccupied passable tile on the battlefield with no regard for distance or obstacles.'
                    },
                    {
                        'name': 'ESTRANGE',
                        'desc': 'Fires a beam that deals defense-piercing damage and reduces all of the target\'s stats.'
                    },
                    {
                        'name': 'GRÆ EXCHANGE',
                        'desc': 'Banishes a target enemy unit and replaces them with a GRAYMAN doppelganger that can attack and explode on death.'
                    }
                ]
            },
            UnitType.MARROW_CONDENSER: {
                'difficulty': 3,  # Out of 5
                'role': 'Tank / Frontline Fighter / Displacer',
                'overview': 'A quadrupedal bone manipulator that creates wall structures to trap enemies. This tank grows stronger with each kill, draining life from trapped enemies while reinforcing its defenses.',
                'passive': {
                    'name': 'DOMINION',
                    'desc': 'When any unit dies within a Marrow Dike interior, absorbs their essence to trigger permanent evolutionary upgrades to stats and active skills. Bonuses are lost on death.'
                },
                'skills': [
                    {
                        'name': 'OSSIFY',
                        'desc': 'Compresses skeletal structure into a nearly impenetrable ossified state, gaining a defense bonus at the cost of reduced movement.'
                    },
                    {
                        'name': 'MARROW DIKE',
                        'desc': 'Erupts bone marrow walls in a perimeter, creating an enclosed killzone. Enemy units on the perimeter are pulled inward, and the walls block movement and line of sight. When upgraded, trapped enemies suffer Mired.'
                    },
                    {
                        'name': 'BONE TITHE',
                        'desc': 'Extracts bone marrow from all adjacent enemies, dealing damage to each and permanently increasing both max and current HP per enemy hit.'
                    }
                ]
            },
            UnitType.GAS_MACHINIST: {
                'difficulty': 5,  # Out of 5
                'role': 'Summoner / Utility / Healer',
                'overview': 'An industrial chemist who deploys autonomous vapor entities in areas that passively affect all units within each turn. This utility specialist excels at area control and sustained support through strategic vapor deployment.',
                'passive': {
                    'name': 'EFFLUVIUM LATHE',
                    'desc': 'Generates charges at the start of each turn. When summoning or splitting vapors, all accumulated charges are consumed to extend vapor duration.'
                },
                'skills': [
                    {
                        'name': 'BROACHING GAS',
                        'desc': 'Expels a vapor that creates a caustic gas cloud. The vapor corrodes enemies within the cloud while randomly dissolving one negative status effect from allies each turn.'
                    },
                    {
                        'name': 'SAFT-E-GAS',
                        'desc': 'Releases a vapor that forms a protective gas shield. The vapor grants defense to allies within the cloud and heals them each turn.'
                    },
                    {
                        'name': 'DIVERGE',
                        'desc': 'Splits an existing vapor or self into two specialized vapor entities. When targeting self, dissolves completely until both vapors expire, then reforms.'
                    },
                    {
                        'name': 'AEROSOLIZE ARMS',
                        'desc': 'Disarms a target and spawns a LIVING AEROSOL under their control. The aerosol inherits the target\'s attack stat. Unlocked by upgrading Effluvium Lathe.'
                    }
                ]
            },
            UnitType.FOWL_CONTRIVANCE: {
                'difficulty': 3,  # Out of 5
                'role': 'Burst Damage / Displacer',
                'overview': 'A mechanical peacock rail artillery platform that transforms the battlefield through devastating long-range bombardment and explosive infrastructure. This heavy artillery excels at indirect fire support and area control.',
                'passive': {
                    'name': 'RAIL GENESIS',
                    'desc': 'The first unit deployed establishes a permanent rail network. When any FOWL CONTRIVANCE dies, the rails detonate, dealing 6 damage to enemies standing on rails. FOWL CONTRIVANCE units are immune to this explosion.'
                },
                'skills': [
                    {
                        'name': 'GAUSSIAN DUSK',
                        'desc': 'Fires a defense-piercing rail cannon across the map in a cardinal direction. Damage follows a bell curve based on target current HP. Destroys terrain at beam midpoint.'
                    },
                    {
                        'name': 'PARABOL',
                        'desc': 'Launches explosive mortar shells that bombard an area. The indirect fire ignores line of sight and deals heavy damage to the center with splash damage around it.'
                    },
                    {
                        'name': 'FRAGCREST',
                        'desc': 'Fires a directional fragmentation burst in a cone. Enemies are knocked back and embedded with shrapnel that damages over time.'
                    }
                ]
            },
            UnitType.DELPHIC_APPRAISER: {
                'difficulty': 4,  # Out of 5
                'role': 'Utility / Displacer / Disabler / Burst Damage / Escape Artist',
                'overview': 'An antique dealer with oracular sight who perceives the astral value of every furniture piece on the battlefield. This utility specialist weaponizes supernatural perception to gain tactical bonuses and manipulate furniture values.',
                'passive': {
                    'name': 'VALUATION ORACLE',
                    'desc': 'Perceives the astral value of every furniture piece. Allies adjacent to high-value furniture gain defense and attack range bonuses.'
                },
                'skills': [
                    {
                        'name': 'MARKET FUTURES',
                        'desc': 'Imbues a furniture piece with investment energy, creating a teleportation locus. The locus lasts a limited number of turns or until activated by an adjacent ally.'
                    },
                    {
                        'name': 'PARALLAX',
                        'desc': 'Appears when adjacent to a Market Futures locus. Instantly teleports the unit up to a distance equal to the locus\'s astral value. Grants increased attack range and growing attack bonuses for a limited duration.'
                    },
                    {
                        'name': 'AUCTION CURSE',
                        'desc': 'Curses the target enemy with sustained damage over time and prevents healing. Nearby furniture values inflate each turn as the curse persists.'
                    },
                    {
                        'name': 'DIVINE DEPRECIATION',
                        'desc': 'Reappraises a furniture piece as worthless, creating a reality sinkhole. Enemies take damage, are pulled inward, and furniture values reroll.'
                    },
                    {
                        'name': 'DEFT(?) REROLL',
                        'icon': 'deft_reroll',
                        'desc': 'Temporarily replaces Divine Depreciation after use. Instantly rerolls all furniture values with wider variance, and increases Divine Depreciation\'s cooldown. Unlocked by upgrading Divine Depreciation.'
                    }
                ]
            },
            UnitType.INTERFERER: {
                'difficulty': 2,  # Out of 5
                'role': 'Burst Damage / Disabler',
                'overview': 'A telecommunications engineer turned assassin who weaponized a remote radio tower array into a directed energy weapon system. This glass cannon coordinates precise strikes, neural hijacking, and electromagnetic warfare.',
                'passive': {
                    'name': 'RADIO EFFULGENT',
                    'desc': 'The antenna array energizes the carabiners, causing RF burn directionally on attack. RF burn stacks deal damage over time.'
                },
                'skills': [
                    {
                        'name': 'NEURAL SHUNT',
                        'desc': 'Transmits a neural interference signal that hijacks the target\'s motor functions, causing them to perform random moves, attacks, or skills.'
                    },
                    {
                        'name': 'KARRIER RAVE',
                        'desc': 'Phases out of reality, becoming untargetable. Upon returning, the stored energy amplifies the next attack to strike three times.'
                    },
                    {
                        'name': 'SCALAR NODE',
                        'desc': 'Creates an invisible energy trap. When any enemy ends their turn on the trapped tile, it detonates and deals damage.'
                    }
                ]
            },
            UnitType.POTPOURRIST: {
                'difficulty': 1,  # Out of 5
                'role': 'Tank / Frontline Fighter',
                'overview': 'A durable tank who wields a heavy granite pedestal as both weapon and incense burner. This unit specializes in persistent regeneration and damage mitigation through disorienting debuffs and magical bindings.',
                'passive': {
                    'name': 'MELANGE EMINENCE',
                    'desc': 'The aromatic blend continuously restores vitality at the start of every turn. This regeneration cannot be prevented.'
                },
                'skills': [
                    {
                        'name': 'INFUSE',
                        'desc': 'Infuses the aromatic blend into concentrated potpourri, intensifying healing vapors and empowering other skills with additional effects.'
                    },
                    {
                        'name': 'DEMILUNE',
                        'desc': 'Swings the granite pedestal in a wide crescent arc, releasing disorienting vapors that cause enemies to deal reduced damage.'
                    },
                    {
                        'name': 'GRANITE GEAS',
                        'desc': 'Strikes an enemy with the pedestal, marking them with a magical binding. If the target fails to attack during their turn, the binding breaks and grants healing.'
                    }
                ]
            },
            UnitType.DERELICTIONIST: {
                'difficulty': 4,  # Out of 5
                'role': 'Utility / Healer / Disabler / Displacer',
                'overview': 'A psychological abandonment therapist who weaponized distance-based therapeutic techniques into a tactical support system. This healer manipulates interpersonal distance to provide powerful healing and protective effects that scale with range.',
                'passive': {
                    'name': 'SEVERANCE',
                    'desc': 'Allows increased movement after being issued a skill or attack. Attack damage is increased by distance. Cannot move twice in one turn.'
                },
                'skills': [
                    {
                        'name': 'VAGAL RUN',
                        'desc': 'Clears all status effects from an ally. At close range deals 1-3 piercing damage that cannot kill. At long range restores HP equal to how far beyond 6 tiles away the DERELICTIONIST is. After 3 turns an abreaction triggers the effect again.'
                    },
                    {
                        'name': 'DERELICT',
                        'desc': 'Forcefully pushes an ally away in a straight line. Applies Derelicted on their arrival, reducing their MV to 0. The ally is healed for 1-15 HP based on the final distance between them and the DERELICTIONIST.'
                    },
                    {
                        'name': 'PARTITION',
                        'desc': 'Creates a protective psychological partition on an ally that reduces incoming damage. If the ally would die while shielded, they dissociate completely to ignore fatal damage. Triggering the dissociation increases Partition\'s cooldown to 6 turns.'
                    }
                ]
            },
            "LANDSCAPER": {
                'difficulty': 5,  # Out of 5
                'role': '??? / ??? / ???',
                'overview': 'A mysterious terrain manipulator with unknown capabilities. Details unknown. Coming soon...',
                'passive': {
                    'name': '???',
                    'desc': 'Placeholder ability description. This unit is not yet available.'
                },
                'skills': [
                    {
                        'name': '???',
                        'desc': 'Placeholder skill description. This unit is not yet available.'
                    },
                    {
                        'name': '???',
                        'desc': 'Placeholder skill description. This unit is not yet available.'
                    },
                    {
                        'name': '???',
                        'desc': 'Placeholder skill description. This unit is not yet available.'
                    }
                ]
            },
            "AETHERIC_CURLER": {
                'difficulty': 5,  # Out of 5
                'role': '??? / ??? / ???',
                'overview': 'A mysterious entity shrouded in aetheric energy. Details unknown. Coming soon...',
                'passive': {
                    'name': '???',
                    'desc': 'Placeholder ability description. This unit is not yet available.'
                },
                'skills': [
                    {
                        'name': '???',
                        'desc': 'Placeholder skill description. This unit is not yet available.'
                    },
                    {
                        'name': '???',
                        'desc': 'Placeholder skill description. This unit is not yet available.'
                    },
                    {
                        'name': '???',
                        'desc': 'Placeholder skill description. This unit is not yet available.'
                    }
                ]
            }
        }

        return simplified_info

    def update(self, unit_type: Optional[UnitType]):
        """Update the displayed unit type."""
        if unit_type != self.unit_type:
            self.unit_type = unit_type
            self.scroll_offset = 0
            self.content_surface = None
            self.show_advanced = False  # Reset to simplified view when changing units

    def handle_click(self, mouse_pos: Tuple[int, int], panel_rect: pygame.Rect) -> bool:
        """
        Handle click on the help panel.
        Returns True if click was inside the panel.
        """
        # Check if clicking the Advanced Details button
        if hasattr(self, 'advanced_button_rect') and self.advanced_button_rect:
            if self.advanced_button_rect.collidepoint(mouse_pos):
                # Toggle to advanced view
                self.show_advanced = True
                self.content_surface = None  # Force re-render
                self.scroll_offset = 0  # Reset scroll
                return True

        return panel_rect.collidepoint(mouse_pos)

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion for button hover effects."""
        if hasattr(self, 'advanced_button_rect') and self.advanced_button_rect:
            self.button_hovered = self.advanced_button_rect.collidepoint(mouse_pos)
        else:
            self.button_hovered = False

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle mouse click on help panel.

        Returns:
            True if click was handled (e.g., button was clicked)
        """
        if hasattr(self, 'advanced_button_rect') and self.advanced_button_rect:
            if self.advanced_button_rect.collidepoint(mouse_pos):
                # Toggle to advanced view
                self.show_advanced = True
                self.content_surface = None
                self.scroll_offset = 0
                return True
        return False

    def handle_scroll(self, scroll_amount: int):
        """
        Handle mouse wheel scroll.

        Args:
            scroll_amount: Positive for scroll up, negative for scroll down
        """
        if self.content_surface:
            scroll_delta = 30 * scroll_amount
            self.scroll_offset = max(0, min(self.scroll_offset - scroll_delta, self.max_scroll))

    def handle_mouse_down(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle mouse button down event for scrollbar.
        Returns True if scrollbar was clicked.
        """
        result = self.scrollbar.handle_mouse_down(mouse_pos)
        if result is not None:
            if isinstance(result, float):
                # Track was clicked, jump to position
                self.scroll_offset = int(result * self.max_scroll)
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            # If result is None, thumb was clicked and drag started automatically
            return True
        return False

    def handle_mouse_up(self):
        """Handle mouse button up event for scrollbar."""
        self.scrollbar.handle_mouse_up()

    def handle_mouse_drag(self, mouse_pos: Tuple[int, int]):
        """Handle mouse motion for scrollbar dragging."""
        new_scroll = self.scrollbar.handle_mouse_motion(mouse_pos, self.scroll_offset, self.max_scroll)
        if new_scroll is not None:
            self.scroll_offset = new_scroll

    def _load_unit_sprite(self, unit_type, size: int = 80) -> Optional[pygame.Surface]:
        """Load unit sprite from SVG at specified size."""
        cache_key = (unit_type, size)
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        # Skip loading for placeholder units (strings)
        if isinstance(unit_type, str):
            self.sprite_cache[cache_key] = None
            return None

        try:
            sprite_name = unit_type.name.lower()
        except AttributeError:
            self.sprite_cache[cache_key] = None
            return None

        sprite_path = asset_path(f"graphics/units/{sprite_name}.svg")

        sprite = load_svg(sprite_path, size, size)
        self.sprite_cache[cache_key] = sprite
        return sprite

    def _load_skill_icon(self, skill_name: str, size: int = 32) -> Optional[pygame.Surface]:
        """Load skill icon from SVG at specified size."""
        cache_key = (skill_name, size)
        if cache_key in self.skill_icon_cache:
            return self.skill_icon_cache[cache_key]

        # Convert skill name to filename
        icon_name = skill_name.lower().replace(' ', '_')
        icon_name = ''.join(c for c in icon_name if c not in r'\/:*?"<>|')
        icon_path = asset_path(f"graphics/skill_icons/{icon_name}.svg")

        icon = load_svg(icon_path, size, size)
        self.skill_icon_cache[cache_key] = icon
        return icon

    def _draw_glaive(self, surface: pygame.Surface, x: int, y: int, size: int, alpha: int, color: tuple):
        """
        Draw a static six-pointed glaive (like from Autoclave animation).

        Args:
            surface: Surface to draw on
            x, y: Center position
            size: Radius of glaive
            alpha: Transparency (0-255)
            color: RGB tuple for glaive color
        """
        import math

        # Six blades radiating from center
        for blade in range(6):
            angle = math.radians(blade * 60)
            # Outer point
            px1 = x + math.cos(angle) * size
            py1 = y + math.sin(angle) * size
            # Inner left
            angle_l = math.radians(blade * 60 - 15)
            px2 = x + math.cos(angle_l) * (size * 0.4)
            py2 = y + math.sin(angle_l) * (size * 0.4)
            # Inner right
            angle_r = math.radians(blade * 60 + 15)
            px3 = x + math.cos(angle_r) * (size * 0.4)
            py3 = y + math.sin(angle_r) * (size * 0.4)

            # Draw blade triangle with alpha
            blade_color = (*color, alpha)
            pygame.draw.polygon(surface, blade_color,
                              [(px1, py1), (px2, py2), (px3, py3)])
            # Bright edge
            edge_color = (255, 255, 255, alpha)
            pygame.draw.polygon(surface, edge_color,
                              [(px1, py1), (px2, py2), (px3, py3)], 1)

        # Center hub
        hub_color = (*color, alpha)
        pygame.draw.circle(surface, hub_color, (int(x), int(y)), int(size * 0.3))
        edge_color = (255, 255, 255, alpha)
        pygame.draw.circle(surface, edge_color, (int(x), int(y)), int(size * 0.3), 2)

    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> list:
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, COLOR_TEXT)

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else ['']

    def _render_simplified_content(self, width: int):
        """Render simplified help content with larger sprites and brief descriptions."""
        if not self.unit_type or self.unit_type not in self.simplified_info:
            return None

        unit_data = self.simplified_info[self.unit_type]

        # Estimate content height
        estimated_height = 1800
        content_surface = pygame.Surface((width, estimated_height), pygame.SRCALPHA)
        content_width = width - 40  # Increased padding to prevent text cutoff
        current_y = 0
        sprite_center_x = width // 2

        # Draw difficulty rating aligned with sprite center
        difficulty = unit_data.get('difficulty', 0)
        diff_label = self.small_font.render("Difficulty Rating", True, COLOR_TEXT_DIM)
        diff_label_rect = diff_label.get_rect(center=(sprite_center_x, current_y + 10))
        content_surface.blit(diff_label, diff_label_rect)
        current_y += 25

        # Draw difficulty indicator (5 glaives) with center glaive aligned to sprite center
        glaive_size = 18
        glaive_spacing = 40
        glaive_y = current_y + 10

        # Check if this is the AETHERIC_CURLER for flashing effect (only this one flashes)
        should_flash = self.unit_type == "AETHERIC_CURLER"

        if should_flash and difficulty == 5:
            # Flash all 5 glaives for max difficulty placeholder
            import time
            import math
            flash_speed = 3.0  # Hz
            alpha = int(128 + 127 * math.sin(time.time() * flash_speed * 2 * math.pi))

            for i in range(5):
                x = sprite_center_x + ((i - 2) * glaive_spacing)
                self._draw_glaive(content_surface, x, glaive_y, glaive_size, alpha, (220, 180, 255))
        else:
            # Normal difficulty indicator
            for i in range(5):
                # Position relative to center glaive
                x = sprite_center_x + ((i - 2) * glaive_spacing)
                if i < difficulty:
                    # Illuminated glaive
                    self._draw_glaive(content_surface, x, glaive_y, glaive_size, 255, (220, 220, 255))
                else:
                    # Dimmed glaive
                    self._draw_glaive(content_surface, x, glaive_y, glaive_size, 60, (100, 100, 100))
        current_y += 40

        # Draw unit sprite (2x larger - 160x160 instead of 80x80)
        # Render directly from SVG at larger size for crisp quality
        large_sprite = self._load_unit_sprite(self.unit_type, size=160)
        if large_sprite:
            sprite_rect = large_sprite.get_rect(center=(sprite_center_x, current_y + 80))
            content_surface.blit(large_sprite, sprite_rect)
        else:
            # Draw placeholder for missing sprite (like for AETHERIC CURLER)
            # Scale placeholder font size based on the passed font size
            placeholder_size = self.font.get_height() * 4  # 4x the normal font height
            placeholder_font = pygame.font.Font(None, placeholder_size)
            placeholder_text = placeholder_font.render("?", True, (180, 140, 200))
            placeholder_rect = placeholder_text.get_rect(center=(sprite_center_x, current_y + 80))
            content_surface.blit(placeholder_text, placeholder_rect)
        current_y += 165

        # Draw unit name
        unit_name = self.unit_names.get(self.unit_type, self._get_unit_name(self.unit_type))
        name_color = (180, 140, 200) if isinstance(self.unit_type, str) else COLOR_GOLD
        title_text = self.font.render(unit_name, True, name_color)
        title_rect = title_text.get_rect(center=(width // 2, current_y))
        content_surface.blit(title_text, title_rect)
        current_y += 25

        # Draw role
        role = unit_data.get('role', '')
        if role:
            role_text = self.small_font.render(role, True, COLOR_TEXT_DIM)
            role_rect = role_text.get_rect(center=(width // 2, current_y))
            content_surface.blit(role_text, role_rect)
            current_y += self._scale_spacing(20)

        # Draw overview (1-2 sentences)
        overview = unit_data.get('overview', '')
        overview_lines = self._wrap_text(overview, content_width, self.small_font)
        for line in overview_lines:
            text_surface = self.small_font.render(line, True, COLOR_TEXT_DIM)
            content_surface.blit(text_surface, (15, current_y))
            current_y += self._scale_spacing(18)  # Increased from 16 for better readability
        current_y += self._scale_spacing(12)

        # Draw separator
        pygame.draw.line(content_surface, COLOR_BORDER, (10, current_y), (width - 10, current_y), 1)
        current_y += self._scale_spacing(12)

        # Draw passive skill
        passive_data = unit_data.get('passive')
        if passive_data:
            passive_label = self.small_font.render("PASSIVE:", True, COLOR_GOLD)
            content_surface.blit(passive_label, (15, current_y))
            current_y += self._scale_spacing(20)

            # Skill name and icon (2x larger - 64x64 instead of 32x32)
            # Render directly from SVG at larger size for crisp quality
            skill_name = passive_data['name']
            large_icon = self._load_skill_icon(skill_name, size=64)

            icon_x = 20
            if large_icon:
                content_surface.blit(large_icon, (icon_x, current_y))
                icon_x += 70

            skill_name_text = self.font.render(skill_name, True, (100, 200, 255))
            content_surface.blit(skill_name_text, (icon_x, current_y + 18))
            current_y += 68

            # Skill description
            desc = passive_data.get('desc', '')
            desc_lines = self._wrap_text(desc, content_width - 10, self.small_font)
            for line in desc_lines:
                desc_text = self.small_font.render(line, True, COLOR_TEXT)
                content_surface.blit(desc_text, (25, current_y))
                current_y += self._scale_spacing(18)  # Increased from 16 for better readability
            current_y += self._scale_spacing(12)

        # Draw separator
        pygame.draw.line(content_surface, COLOR_BORDER, (10, current_y), (width - 10, current_y), 1)
        current_y += self._scale_spacing(12)

        # Draw active skills
        skills = unit_data.get('skills', [])
        if skills:
            skills_label = self.small_font.render("ACTIVE SKILLS:", True, COLOR_GOLD)
            content_surface.blit(skills_label, (15, current_y))
            current_y += self._scale_spacing(20)

            for skill_data in skills:
                # Skill name and icon (2x larger)
                # Render directly from SVG at larger size for crisp quality
                skill_name = skill_data['name']
                if 'icon' in skill_data:
                    large_icon = self._load_skill_icon(skill_data['icon'], size=64)
                else:
                    large_icon = self._load_skill_icon(skill_name, size=64)

                icon_x = 20
                if large_icon:
                    content_surface.blit(large_icon, (icon_x, current_y))
                    icon_x += 70

                skill_name_text = self.font.render(skill_name, True, (100, 200, 255))
                content_surface.blit(skill_name_text, (icon_x, current_y + 18))
                current_y += 68

                # Skill description
                desc = skill_data.get('desc', '')
                desc_lines = self._wrap_text(desc, content_width - 10, self.small_font)
                for line in desc_lines:
                    desc_text = self.small_font.render(line, True, COLOR_TEXT)
                    content_surface.blit(desc_text, (25, current_y))
                    current_y += self._scale_spacing(18)  # Increased from 16 for better readability
                current_y += self._scale_spacing(10)  # Increased from 8

        # Trim to actual height
        actual_height = current_y + 10
        trimmed_surface = pygame.Surface((width, actual_height), pygame.SRCALPHA)
        trimmed_surface.blit(content_surface, (0, 0))

        return trimmed_surface

    def _render_content(self, width: int):
        """Render full help content to a surface."""
        if not self.unit_type or self.unit_type not in self.unit_help_data:
            return None

        unit_data = self.unit_help_data[self.unit_type]

        # Estimate content height
        estimated_height = 3500
        content_surface = pygame.Surface((width, estimated_height), pygame.SRCALPHA)
        content_width = width - 40  # Increased padding to prevent text cutoff
        current_y = 0

        # Draw unit sprite (centered at top)
        sprite = self._load_unit_sprite(self.unit_type)
        if sprite:
            sprite_rect = sprite.get_rect(center=(width // 2, current_y + 40))
            content_surface.blit(sprite, sprite_rect)
        current_y += 90

        # Draw unit title
        title_text = self.font.render(unit_data['title'], True, COLOR_GOLD)
        title_rect = title_text.get_rect(center=(width // 2, current_y))
        content_surface.blit(title_text, title_rect)
        current_y += self._scale_spacing(30)

        # Draw overview
        for line in unit_data.get('overview', []):
            if line:
                wrapped_lines = self._wrap_text(line, content_width, self.small_font)
                for wrapped in wrapped_lines:
                    text_surface = self.small_font.render(wrapped, True, COLOR_TEXT_DIM)
                    content_surface.blit(text_surface, (15, current_y))
                    current_y += self._scale_spacing(18)
            else:
                current_y += self._scale_spacing(10)
        current_y += self._scale_spacing(15)

        # Draw stats
        stats_heading = self.font.render("BASE STATS", True, COLOR_GOLD)
        content_surface.blit(stats_heading, (15, current_y))
        current_y += self._scale_spacing(25)

        for stat in unit_data.get('stats', []):
            stat_text = self.small_font.render(stat, True, COLOR_TEXT_DIM)
            content_surface.blit(stat_text, (20, current_y))
            current_y += self._scale_spacing(18)

        current_y += self._scale_spacing(20)

        # Draw separator
        pygame.draw.line(content_surface, COLOR_BORDER, (10, current_y), (width - 10, current_y), 2)
        current_y += self._scale_spacing(20)

        # Draw skills
        skills_heading = self.font.render("SKILLS", True, COLOR_GOLD)
        content_surface.blit(skills_heading, (15, current_y))
        current_y += self._scale_spacing(25)

        for skill_data in unit_data.get('skills', []):
            # Skill name and icon
            skill_name = skill_data['name']
            # Extract skill name without (Passive/Active) and [Key: X]
            skill_icon_name = skill_name.split(' (')[0]
            skill_icon = self._load_skill_icon(skill_icon_name)

            icon_x = 20
            if skill_icon:
                content_surface.blit(skill_icon, (icon_x, current_y))
                icon_x += 38

            skill_name_text = self.font.render(skill_name, True, (100, 200, 255))
            content_surface.blit(skill_name_text, (icon_x, current_y + 5))
            current_y += self._scale_spacing(35)

            # Skill description
            desc = skill_data.get('description', '')
            desc_lines = self._wrap_text(desc, content_width - 10, self.small_font)
            for line in desc_lines:
                desc_text = self.small_font.render(line, True, COLOR_TEXT)
                content_surface.blit(desc_text, (25, current_y))
                current_y += self._scale_spacing(18)

            current_y += self._scale_spacing(5)

            # Skill details (bullets)
            for detail in skill_data.get('details', []):
                detail_text = self.small_font.render(f"  • {detail}", True, COLOR_TEXT_DIM)
                content_surface.blit(detail_text, (30, current_y))
                current_y += self._scale_spacing(18)

            current_y += self._scale_spacing(15)

        # Draw separator
        pygame.draw.line(content_surface, COLOR_BORDER, (10, current_y), (width - 10, current_y), 2)
        current_y += self._scale_spacing(20)

        # Draw combat tips
        if 'tips' in unit_data and unit_data['tips']:
            tips_heading = self.font.render("COMBAT TIPS", True, COLOR_GOLD)
            content_surface.blit(tips_heading, (15, current_y))
            current_y += self._scale_spacing(25)

            for tip in unit_data['tips']:
                wrapped_tip = self._wrap_text(tip, content_width - 10, self.small_font)
                for wrapped in wrapped_tip:
                    tip_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                    content_surface.blit(tip_text, (20, current_y))
                    current_y += self._scale_spacing(18)
                current_y += self._scale_spacing(5)

            current_y += self._scale_spacing(15)

        # Draw tactical notes
        if 'tactical' in unit_data and unit_data['tactical']:
            tactical_heading = self.font.render("TACTICAL NOTES", True, COLOR_GOLD)
            content_surface.blit(tactical_heading, (15, current_y))
            current_y += self._scale_spacing(25)

            for note in unit_data['tactical']:
                wrapped_note = self._wrap_text(note, content_width - 10, self.small_font)
                for wrapped in wrapped_note:
                    note_text = self.small_font.render(wrapped, True, COLOR_TEXT)
                    content_surface.blit(note_text, (20, current_y))
                    current_y += self._scale_spacing(18)
                current_y += self._scale_spacing(5)

        # Trim to actual height
        actual_height = current_y + 20
        trimmed_surface = pygame.Surface((width, actual_height), pygame.SRCALPHA)
        trimmed_surface.blit(content_surface, (0, 0))

        return trimmed_surface

    def draw(self, screen: pygame.Surface, x: int, y: int, width: int, height: int) -> pygame.Rect:
        """
        Draw the help panel.

        Args:
            screen: Pygame screen surface
            x, y: Position (top-left)
            width, height: Panel dimensions

        Returns:
            Panel rectangle for click detection
        """
        # Always draw the panel background
        panel_rect = pygame.Rect(x, y, width, height)

        # Highlight border if focused
        border_color = (150, 200, 255) if self.has_focus else COLOR_BORDER
        pygame.draw.rect(screen, COLOR_BG, panel_rect)
        pygame.draw.rect(screen, border_color, panel_rect, 2)

        if not self.unit_type:
            # Show "Click a unit" message
            no_unit_text = self.font.render("Click a unit to view details", True, COLOR_TEXT_DIM)
            no_unit_rect = no_unit_text.get_rect(center=(x + width // 2, y + height // 2))
            screen.blit(no_unit_text, no_unit_rect)
            return panel_rect

        # Check if this is AETHERIC_CURLER that needs animation (flashing glaives)
        needs_animation = self.unit_type == "AETHERIC_CURLER"

        # Render content if needed (choose simplified or full based on show_advanced flag)
        # For AETHERIC_CURLER, always re-render to animate the flashing glaives
        # Use full width since scrollbar will be positioned outside panel
        if not self.content_surface or (needs_animation and not self.show_advanced):
            if self.show_advanced:
                # Check if full help data exists
                if self.unit_type not in self.unit_help_data:
                    unit_name = self._get_unit_name(self.unit_type)
                    error_text = self.small_font.render(f"No help data for {unit_name}", True, (255, 100, 100))
                    screen.blit(error_text, (x + 15, y + 15))
                    return panel_rect
                self.content_surface = self._render_content(width)
            else:
                # Check if simplified data exists
                if self.unit_type not in self.simplified_info:
                    unit_name = self._get_unit_name(self.unit_type)
                    error_text = self.small_font.render(f"No info for {unit_name}", True, (255, 100, 100))
                    screen.blit(error_text, (x + 15, y + 15))
                    return panel_rect
                self.content_surface = self._render_simplified_content(width)

        if not self.content_surface:
            return panel_rect

        # Draw "Advanced Details" button at top if in simplified view
        button_rect = None
        if not self.show_advanced:
            button_width = 160
            button_height = 30
            button_x = x + width - button_width - 15
            button_y = y + 10
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

            # Button background
            button_color = (70, 110, 150) if not hasattr(self, 'button_hovered') or not self.button_hovered else (90, 130, 170)
            pygame.draw.rect(screen, button_color, button_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 150, 200), button_rect, 2, border_radius=5)

            # Button text
            button_text = self.small_font.render("Advanced Details", True, COLOR_TEXT)
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)

            # Store button rect for click detection
            self.advanced_button_rect = button_rect

            # Adjust content area to not overlap button
            content_start_y = y + 50
            visible_height = height - 60
        else:
            self.advanced_button_rect = None
            content_start_y = y + 10
            visible_height = height - 20

        # Calculate scroll limits
        content_height = self.content_surface.get_height()
        self.max_scroll = max(0, content_height - visible_height)

        # Set up clipping region (use full width, scrollbar outside)
        content_rect = pygame.Rect(x + 10, content_start_y, width - 20, visible_height)
        screen.set_clip(content_rect)

        # Draw content with scroll offset
        screen.blit(self.content_surface, (x + 10, content_start_y - self.scroll_offset))

        # Clear clipping
        screen.set_clip(None)

        # Draw scrollbar if needed (position outside panel, to the right)
        scrollbar_x = x + width + 5  # Position outside panel with small gap
        self.scrollbar.draw(screen, scrollbar_x, content_start_y, visible_height,
                           self.scroll_offset, self.max_scroll, visible_height, content_height)

        return panel_rect
