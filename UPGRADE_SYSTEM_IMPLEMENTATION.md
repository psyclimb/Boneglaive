# Boneglaive Upgrade System - Implementation Plan

## System Overview

Players earn upgrade points at GP thresholds (2 GP = 1 point, 4 GP = 1 point, win at 6 GP). Points can be banked and spent anytime during player's turn to upgrade skills/passives on their units. Upgrades are permanent and apply enhanced effects (damage increases, range boosts) or side-grades (alternative effects).

---

## Phase 1: Backend Core System

### 1.1 Add Upgrade Point Tracking to Game Class

**File**: `boneglaive/game/engine.py`

**Location**: Lines 50-52 (next to GP tracking)

**Changes**:
```python
# In Game.__init__
self.player1_gp = 0
self.player2_gp = 0
self.gp_win_threshold = 3  # Will be changed to 6

# ADD THESE:
self.player1_upgrade_points = 0
self.player2_upgrade_points = 0
self.upgrade_point_thresholds = [2, 4]  # GP thresholds for earning points
self.upgrade_points_awarded = {1: set(), 2: set()}  # Track which thresholds already awarded per player
```

**Why**: Centralizes upgrade point state next to existing GP tracking. Uses set to prevent double-awarding if GP fluctuates.

---

### 1.2 Award Upgrade Points at GP Thresholds

**File**: `boneglaive/game/engine.py`

**Location**: In `handle_unit_death()` method, after GP award logic (around line 1800-1863)

**Current Pattern** (from DOMINION reference):
```python
# GP is awarded in Unit._handle_death() in units.py (lines 850-860)
# Then handle_unit_death() is called in engine.py
```

**Add After GP Award**:
```python
def handle_unit_death(self, dead_unit, killer, cause="unknown", ui=None):
    # ... existing death handling code ...

    # After GP is awarded to killer's player
    killer_player = killer.player
    current_gp = self.player1_gp if killer_player == 1 else self.player2_gp

    # Check if player crossed any upgrade thresholds
    for threshold in self.upgrade_point_thresholds:
        # Award point if threshold reached and not already awarded
        if current_gp >= threshold and threshold not in self.upgrade_points_awarded[killer_player]:
            # Award upgrade point
            if killer_player == 1:
                self.player1_upgrade_points += 1
            else:
                self.player2_upgrade_points += 1

            # Mark threshold as awarded
            self.upgrade_points_awarded[killer_player].add(threshold)

            # Log message
            message_log.add_message(
                f"Player {killer_player} earned 1 upgrade point! ({current_gp} GP)",
                MessageType.SYSTEM,
                player=killer_player
            )
```

**Why**: Awards points automatically when thresholds are reached. Set tracking prevents double-awards.

---

### 1.3 Create Upgrade Registry and Manager

**File**: `boneglaive/game/upgrades.py` (NEW FILE)

**Purpose**: Centralize all upgrade definitions and upgrade application logic.

**Structure**:
```python
#!/usr/bin/env python3
"""
Upgrade System for Boneglaive
Defines skill and passive upgrades for all units.
"""

from typing import Optional, Dict, List, Set
from boneglaive.utils.message_log import message_log, MessageType

# ============================================================================
# UPGRADE DEFINITIONS
# ============================================================================

SKILL_UPGRADES = {
    # Format: "UNIT_TYPE_NAME": { "SkillName": { upgrade_def }, ... }

    "GLAIVEMAN": {
        "Judgement": {
            "name": "Divine Judgement",
            "description": "Damage increases from 4/8 to 6/12. Range increases from 4 to 5.",
            "type": "buff",  # 'buff' or 'sidegrade'
            "cost": 1
        },
        "Vault": {
            "name": "Extended Vault",
            "description": "Range increases from 2 to 3.",
            "type": "buff",
            "cost": 1
        },
        "Pry": {
            "name": "Devastating Pry",
            "description": "Primary damage increases from 6 to 8. Splash damage increases from 3 to 4.",
            "type": "buff",
            "cost": 1
        },
        "Autoclave": {  # Passive
            "name": "Autoclave Overdrive",
            "description": "Can trigger twice per game instead of once.",
            "type": "buff",
            "cost": 1
        }
    },

    "MANDIBLE_FOREMAN": {
        "Expedite": {
            "name": "Hydraulic Charge",
            "description": "Damage increases from 6 to 8. Range increases from 4 to 5.",
            "type": "buff",
            "cost": 1
        },
        "Site Inspection": {
            "name": "Expert Inspection",
            "description": "Buff duration increases from 3 turns to 4 turns.",
            "type": "buff",
            "cost": 1
        },
        "Jawline": {
            "name": "Reinforced Jawline",
            "description": "Damage increases from 4 to 6. Immobilization duration increases from 2 to 3 turns.",
            "type": "buff",
            "cost": 1
        },
        "Viseroy": {  # Passive
            "name": "Industrial Crusher",
            "description": "Jaws deal +1 damage per turn (stacking).",
            "type": "buff",
            "cost": 1
        }
    },

    "GRAYMAN": {
        "Delta Config": {
            "name": "Quantum Fold",
            "description": "Cooldown reduces from 12 turns to 9 turns.",
            "type": "buff",
            "cost": 1
        },
        "Estrange": {
            "name": "Deep Estrangement",
            "description": "Stat reduction increases from -1 to -2 per stack.",
            "type": "buff",
            "cost": 1
        },
        "Græ Exchange": {
            "name": "Stable Echo",
            "description": "Echo HP increases from 5 to 8. Echo persists for 3 turns instead of 2.",
            "type": "buff",
            "cost": 1
        },
        "Stasiality": {  # Passive - SIDEGRADE example
            "name": "Phase Shift",
            "description": "Can move through units and terrain (but remains targetable).",
            "type": "sidegrade",
            "cost": 1
        }
    },

    # TODO: Add remaining units (MARROW_CONDENSER, FOWL_CONTRIVANCE, GAS_MACHINIST,
    #       DELPHIC_APPRAISER, INTERFERER, DERELICTIONIST, POTPOURRIST)
    # NOTE: MARROW_CONDENSER already has DOMINION upgrade system - integrate that differently
}

# ============================================================================
# UPGRADE MANAGER CLASS
# ============================================================================

class UpgradeManager:
    """Manages skill and passive upgrades for units."""

    @staticmethod
    def can_afford_upgrade(game, player: int, upgrade_cost: int = 1) -> bool:
        """Check if player has enough upgrade points."""
        points = game.player1_upgrade_points if player == 1 else game.player2_upgrade_points
        return points >= upgrade_cost

    @staticmethod
    def get_available_upgrades(unit) -> List[Dict]:
        """
        Get list of upgrades available for this unit.
        Returns list of dicts with: skill_name, name, description, type, cost
        """
        from boneglaive.utils.constants import UnitType

        # Get unit type name
        unit_type_name = None
        for ut in UnitType:
            if ut.value == unit.type:
                unit_type_name = ut.name
                break

        if not unit_type_name or unit_type_name not in SKILL_UPGRADES:
            return []

        upgrades = []
        for skill_name, upgrade_def in SKILL_UPGRADES[unit_type_name].items():
            # Check if not already upgraded
            if hasattr(unit, 'upgraded_skills') and skill_name in unit.upgraded_skills:
                continue

            upgrades.append({
                'skill_name': skill_name,
                'name': upgrade_def['name'],
                'description': upgrade_def['description'],
                'type': upgrade_def['type'],
                'cost': upgrade_def['cost']
            })

        return upgrades

    @staticmethod
    def apply_upgrade(unit, skill_name: str, game) -> bool:
        """
        Apply an upgrade to a unit's skill.
        Returns True if successful, False if upgrade failed.
        """
        # Verify unit has upgraded_skills attribute
        if not hasattr(unit, 'upgraded_skills'):
            unit.upgraded_skills = set()

        # Check if already upgraded
        if skill_name in unit.upgraded_skills:
            return False

        # Check if player can afford
        upgrade_cost = 1  # All upgrades cost 1 for now
        if not UpgradeManager.can_afford_upgrade(game, unit.player, upgrade_cost):
            return False

        # Apply upgrade
        unit.upgraded_skills.add(skill_name)

        # Deduct upgrade point
        if unit.player == 1:
            game.player1_upgrade_points -= upgrade_cost
        else:
            game.player2_upgrade_points -= upgrade_cost

        # Log upgrade message
        from boneglaive.utils.constants import UnitType
        unit_type_name = None
        for ut in UnitType:
            if ut.value == unit.type:
                unit_type_name = ut.name
                break

        upgrade_name = "Unknown"
        if unit_type_name in SKILL_UPGRADES and skill_name in SKILL_UPGRADES[unit_type_name]:
            upgrade_name = SKILL_UPGRADES[unit_type_name][skill_name]['name']

        message_log.add_message(
            f"Player {unit.player} upgraded {unit.get_display_name()}'s {skill_name} → {upgrade_name}",
            MessageType.SYSTEM,
            player=unit.player
        )

        return True

    @staticmethod
    def is_skill_upgraded(unit, skill_name: str) -> bool:
        """Check if a specific skill is upgraded on this unit."""
        return hasattr(unit, 'upgraded_skills') and skill_name in unit.upgraded_skills
```

**Why**: Single source of truth for all upgrades. UpgradeManager handles all upgrade logic consistently.

---

### 1.4 Add Upgrade State to Unit Class

**File**: `boneglaive/game/units.py`

**Location**: In `Unit.__init__()` (around line 16+)

**Changes**:
```python
class Unit:
    def __init__(self, unit_type, player, y, x):
        # ... existing initialization ...

        # Upgrade tracking (NEW)
        self.upgraded_skills = set()  # Set of skill names that have been upgraded

        # NOTE: Passives use the same set - just add passive name to upgraded_skills
```

**Why**: Per-unit storage is simplest. Set allows fast membership checking. Persists through respawn (need to handle that separately).

---

### 1.5 Add Upgrade Application Method to Game

**File**: `boneglaive/game/engine.py`

**Location**: Add new method (anywhere in Game class, suggest near other helper methods)

**Code**:
```python
def apply_unit_upgrade(self, unit, skill_name: str) -> bool:
    """
    Apply an upgrade to a unit. Called from UI when player confirms upgrade.
    Returns True if successful, False otherwise.
    """
    from boneglaive.game.upgrades import UpgradeManager
    return UpgradeManager.apply_upgrade(unit, skill_name, self)
```

**Why**: Provides clean API for UI to apply upgrades. Delegates to UpgradeManager.

---

## Phase 2: Test with 2-3 Units

### 2.1 Update GLAIVEMAN Skills to Check for Upgrades

**Files**:
- `boneglaive/game/skills/glaiveman.py`

**Pattern for Each Skill**:

**Judgement Skill** (example):
```python
class JudgementSkill(ActiveSkill):
    def __init__(self):
        super().__init__(
            name="Judgement",
            key="J",
            description="...",
            target_type=TargetType.SINGLE,
            cooldown=4,
            range_=4
        )
        self.base_damage = 4
        self.crit_damage = 8
        self.upgraded = False  # Track upgrade status for current execution

    def execute(self, user, target_pos, game, ui=None):
        # CHECK FOR UPGRADE
        from boneglaive.game.upgrades import UpgradeManager
        self.upgraded = UpgradeManager.is_skill_upgraded(user, self.name)

        # Apply upgrade effects
        if self.upgraded:
            self.base_damage = 6  # Upgraded from 4
            self.crit_damage = 12  # Upgraded from 8
            self.range_ = 5  # Upgraded from 4
        else:
            self.base_damage = 4
            self.crit_damage = 8
            self.range_ = 4

        # Rest of existing execution code...
        # (use self.base_damage and self.crit_damage instead of hardcoded values)
```

**Vault Skill** (example):
```python
class VaultSkill(ActiveSkill):
    def __init__(self):
        super().__init__(
            name="Vault",
            key="V",
            description="...",
            target_type=TargetType.POSITION,
            cooldown=4,
            range_=2
        )
        self.upgraded = False

    def execute(self, user, target_pos, game, ui=None):
        # CHECK FOR UPGRADE
        from boneglaive.game.upgrades import UpgradeManager
        self.upgraded = UpgradeManager.is_skill_upgraded(user, self.name)

        # Apply upgrade effects
        if self.upgraded:
            self.range_ = 3  # Upgraded from 2
        else:
            self.range_ = 2

        # Rest of existing execution code...
```

**Autoclave Passive** (example):
```python
class Autoclave(PassiveSkill):
    def __init__(self):
        super().__init__(
            name="Autoclave",
            key="A",
            description="..."
        )
        self.activated = False
        self.max_activations = 1  # Base: 1 activation
        self.activations_used = 0
        self.upgraded = False

    def can_activate(self, user) -> bool:
        # CHECK FOR UPGRADE
        from boneglaive.game.upgrades import UpgradeManager
        self.upgraded = UpgradeManager.is_skill_upgraded(user, self.name)

        # Apply upgrade effects
        if self.upgraded:
            self.max_activations = 2  # Upgraded: 2 activations
        else:
            self.max_activations = 1

        return self.activations_used < self.max_activations
```

**Apply this pattern to**: Pry, Vault, Judgement, Autoclave (all GLAIVEMAN skills)

---

### 2.2 Update MANDIBLE_FOREMAN Skills

**Files**:
- `boneglaive/game/skills/mandible_foreman.py`

**Apply same pattern to**: Expedite, Site Inspection, Jawline, Viseroy

**Expedite Example**:
```python
def execute(self, user, target_pos, game, ui=None):
    from boneglaive.game.upgrades import UpgradeManager
    self.upgraded = UpgradeManager.is_skill_upgraded(user, self.name)

    # Upgraded damage and range
    damage = 8 if self.upgraded else 6
    max_range = 5 if self.upgraded else 4

    # Rest of execution...
```

---

### 2.3 Update GRAYMAN Skills

**Files**:
- `boneglaive/game/skills/grayman.py`

**Apply same pattern to**: Delta Config, Estrange, Græ Exchange, Stasiality

**Stasiality Sidegrade Example** (more complex):
```python
class Stasiality(PassiveSkill):
    def __init__(self):
        super().__init__(
            name="Stasiality",
            key="S",
            description="..."
        )
        self.upgraded = False
        self.phase_shift_active = False  # Sidegrade: can move through obstacles

    def apply_passive(self, user, game=None, ui=None):
        from boneglaive.game.upgrades import UpgradeManager
        self.upgraded = UpgradeManager.is_skill_upgraded(user, self.name)

        if self.upgraded:
            # Sidegrade: Enable phase shift (check this in movement validation)
            user.can_phase_shift = True
        else:
            user.can_phase_shift = False
```

**NOTE**: Sidegrade effects like "move through terrain" require integration with movement system. May defer this specific upgrade.

---

### 2.4 Manual Testing (No UI Yet)

**Test Script** (run in Python REPL or create test file):
```python
# Force GP to 2 for player 1
game.player1_gp = 2
game.handle_unit_death(some_dead_unit, killer_unit, "test")

# Verify upgrade point awarded
assert game.player1_upgrade_points == 1

# Get a unit and check available upgrades
unit = game.get_unit_at(3, 3)  # GLAIVEMAN at some position
from boneglaive.game.upgrades import UpgradeManager
upgrades = UpgradeManager.get_available_upgrades(unit)
print(upgrades)  # Should show Judgement, Vault, Pry, Autoclave

# Apply upgrade
success = game.apply_unit_upgrade(unit, "Judgement")
assert success == True
assert game.player1_upgrade_points == 0
assert "Judgement" in unit.upgraded_skills

# Use skill and verify upgraded behavior
# (manual playtesting)
```

---

## Phase 3: ASCII UI

### 3.1 Display Upgrade Points in Status Bar

**File**: `boneglaive/ui/game_ui.py` (or wherever status bar is drawn)

**Location**: Find where GP is displayed (search for "GP:" or similar)

**Changes**:
```python
# Find existing GP display code
gp_text = f"GP: {current_gp}/{threshold}"

# Add upgrade points display
upgrade_points = game.player1_upgrade_points if game.current_player == 1 else game.player2_upgrade_points
status_text = f"{gp_text} | UP: {upgrade_points}"  # UP = Upgrade Points

# Render status_text
```

**Why**: Players need to see how many upgrade points they have available.

---

### 3.2 Create Upgrade Menu Component

**File**: `boneglaive/ui/ui_components.py`

**Location**: Add new class at end of file (after existing components)

**Code**:
```python
class UpgradeMenuComponent(UIComponent):
    """Component for displaying and selecting upgrades during gameplay."""

    def __init__(self, renderer, game_ui):
        super().__init__(renderer, game_ui)
        self.show_upgrade_menu = False
        self.selected_unit = None
        self.available_upgrades = []
        self.scroll_offset = 0

    def open_menu(self, unit):
        """Open upgrade menu for the specified unit."""
        from boneglaive.game.upgrades import UpgradeManager

        self.selected_unit = unit
        self.available_upgrades = UpgradeManager.get_available_upgrades(unit)

        if len(self.available_upgrades) == 0:
            message_log.add_message(
                "No upgrades available for this unit.",
                MessageType.WARNING,
                player=unit.player
            )
            return

        self.show_upgrade_menu = True
        self.scroll_offset = 0

    def close_menu(self):
        """Close the upgrade menu."""
        self.show_upgrade_menu = False
        self.selected_unit = None
        self.available_upgrades = []

    def draw(self):
        """Draw the upgrade menu overlay."""
        if not self.show_upgrade_menu or not self.selected_unit:
            return

        # Get terminal dimensions
        max_y, max_x = self.renderer.stdscr.getmaxyx()

        # Calculate menu dimensions (centered)
        menu_width = 70
        menu_height = min(20, len(self.available_upgrades) + 5)
        start_y = (max_y - menu_height) // 2
        start_x = (max_x - menu_width) // 2

        # Draw menu background
        for y in range(start_y, start_y + menu_height):
            self.renderer.stdscr.addstr(y, start_x, " " * menu_width, curses.A_REVERSE)

        # Draw title
        title = f"Upgrade {self.selected_unit.get_display_name()}"
        self.renderer.stdscr.addstr(start_y + 1, start_x + 2, title, curses.A_BOLD | curses.A_REVERSE)

        # Draw upgrade points available
        game = self.game_ui.game
        points = game.player1_upgrade_points if self.selected_unit.player == 1 else game.player2_upgrade_points
        points_text = f"Upgrade Points: {points}"
        self.renderer.stdscr.addstr(start_y + 2, start_x + 2, points_text, curses.A_REVERSE)

        # Draw available upgrades
        hotkeys = ['Q', 'W', 'E', 'R', 'T', 'Y']  # Up to 6 upgrades
        for i, upgrade in enumerate(self.available_upgrades):
            if i >= len(hotkeys):
                break  # Max 6 upgrades displayable

            y_pos = start_y + 4 + i
            hotkey = hotkeys[i]
            upgrade_text = f"[{hotkey}] {upgrade['name']}"
            desc_text = f"    {upgrade['description']}"

            # Draw upgrade option
            self.renderer.stdscr.addstr(y_pos, start_x + 2, upgrade_text, curses.A_BOLD | curses.A_REVERSE)
            self.renderer.stdscr.addstr(y_pos + 1, start_x + 2, desc_text, curses.A_REVERSE)

        # Draw instructions
        instructions = "[ESC] Cancel"
        self.renderer.stdscr.addstr(
            start_y + menu_height - 2,
            start_x + 2,
            instructions,
            curses.A_DIM | curses.A_REVERSE
        )

        self.renderer.stdscr.refresh()

    def handle_input(self, key: int) -> bool:
        """Handle input for upgrade menu."""
        if not self.show_upgrade_menu:
            return False

        # ESC to cancel
        if key == 27:  # ESC
            self.close_menu()
            return True

        # Hotkey selection (Q=0, W=1, E=2, R=3, T=4, Y=5)
        hotkey_map = {
            ord('q'): 0, ord('Q'): 0,
            ord('w'): 1, ord('W'): 1,
            ord('e'): 2, ord('E'): 2,
            ord('r'): 3, ord('R'): 3,
            ord('t'): 4, ord('T'): 4,
            ord('y'): 5, ord('Y'): 5,
        }

        if key in hotkey_map:
            idx = hotkey_map[key]
            if idx < len(self.available_upgrades):
                # Apply upgrade
                upgrade = self.available_upgrades[idx]
                game = self.game_ui.game
                success = game.apply_unit_upgrade(self.selected_unit, upgrade['skill_name'])

                if success:
                    message_log.add_message(
                        f"Upgraded {upgrade['skill_name']}!",
                        MessageType.SYSTEM,
                        player=self.selected_unit.player
                    )
                    self.close_menu()
                else:
                    message_log.add_message(
                        "Failed to apply upgrade.",
                        MessageType.WARNING,
                        player=self.selected_unit.player
                    )

                return True

        return False
```

**Why**: Provides full-screen upgrade selection interface with hotkeys.

---

### 3.3 Integrate Upgrade Menu into Game UI

**File**: `boneglaive/ui/game_ui.py` (main UI class)

**Changes**:

1. **Initialize Component**:
```python
class GameUI:
    def __init__(self, stdscr, game):
        # ... existing components ...

        # Add upgrade menu component
        self.upgrade_menu = UpgradeMenuComponent(self.renderer, self)
```

2. **Add Hotkey Handler** (U key):
```python
def handle_input(self, key):
    # Check if upgrade menu is open (priority)
    if self.upgrade_menu.show_upgrade_menu:
        if self.upgrade_menu.handle_input(key):
            return

    # ... existing input handling ...

    # U key - Open upgrade menu for selected unit
    if key == ord('u') or key == ord('U'):
        if self.selected_unit and self.selected_unit.player == self.game.current_player:
            self.upgrade_menu.open_menu(self.selected_unit)
        else:
            message_log.add_message(
                "Select one of your units to upgrade.",
                MessageType.WARNING,
                player=self.game.current_player
            )
        return
```

3. **Draw Upgrade Menu**:
```python
def draw(self):
    # ... existing draw calls ...

    # Draw upgrade menu on top (if open)
    self.upgrade_menu.draw()
```

**Why**: Integrates upgrade menu into existing UI flow. U key opens menu when unit selected.

---

## Phase 4: Graphical UI

### 4.1 Display Upgrade Points in Top Bar

**File**: `boneglaive/graphical/ui/top_bar.py`

**Location**: Lines 35-36 (add to __init__), Lines 63-64 (add to update())

**Changes**:

1. **Add to __init__**:
```python
def __init__(self, font, small_font):
    # ... existing init ...

    # Upgrade points tracking (NEW)
    self.player1_upgrade_points = 0
    self.player2_upgrade_points = 0
```

2. **Add to update()**:
```python
def update(self, game_adapter):
    # ... existing update code ...

    # Update upgrade points (NEW)
    if game_adapter.game:
        self.player1_upgrade_points = game_adapter.game.player1_upgrade_points
        self.player2_upgrade_points = game_adapter.game.player2_upgrade_points
```

3. **Update draw() to show upgrade points**:
```python
def draw(self, surface):
    # ... existing GP display code ...

    # Draw upgrade points next to GP
    # For Player 1 (left side)
    up_text_p1 = f"UP: {self.player1_upgrade_points}"
    up_surface_p1 = self.small_font.render(up_text_p1, True, (180, 200, 255))
    surface.blit(up_surface_p1, (gp_x + 150, gp_y))  # Adjust position as needed

    # For Player 2 (right side)
    up_text_p2 = f"UP: {self.player2_upgrade_points}"
    up_surface_p2 = self.small_font.render(up_text_p2, True, (255, 180, 180))
    surface.blit(up_surface_p2, (screen_width - up_x - 150, gp_y))  # Adjust position as needed
```

**Why**: Shows upgrade points prominently in top bar next to GP display.

---

### 4.2 Enable UPGRADE Button in Action Menu

**File**: `boneglaive/graphical/ui/action_menu.py`

**Location**: In `update()` method (around line 141-193)

**Changes**:
```python
def update(self, selected_unit, current_mode, game):
    # ... existing button enable/disable logic ...

    # NEW: Handle UPGRADE button
    elif button.action == "upgrade":
        has_upgrades = False
        has_points = False

        if selected_unit and game:
            from boneglaive.game.upgrades import UpgradeManager

            # Check if unit has available upgrades
            available = UpgradeManager.get_available_upgrades(selected_unit)
            has_upgrades = len(available) > 0

            # Check if player has upgrade points
            has_points = UpgradeManager.can_afford_upgrade(game, selected_unit.player, 1)

        button.enabled = (has_upgrades and has_points)
        button.active = (current_mode == "upgrade")
```

**Why**: UPGRADE button already exists! Just need to enable it when conditions are met.

---

### 4.3 Create Upgrade Window Component

**File**: `boneglaive/graphical/ui/upgrade_window.py` (NEW FILE)

**Purpose**: Modal window for selecting upgrades (similar to respawn_window.py)

**Code**:
```python
#!/usr/bin/env python3
"""
Upgrade Window Component
Modal window for selecting unit upgrades during gameplay.
"""

import pygame
from typing import Optional, List, Dict

# Colors
COLOR_BG = (30, 34, 42)
COLOR_BORDER = (100, 100, 100)
COLOR_TITLE_BG = (40, 44, 52)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)
COLOR_BUTTON = (60, 70, 80)
COLOR_BUTTON_HOVER = (80, 90, 100)
COLOR_BUTTON_DISABLED = (40, 45, 50)
COLOR_GREEN = (100, 255, 150)
COLOR_GOLD = (255, 215, 0)


class UpgradeWindow:
    """Modal window for selecting upgrades for a unit."""

    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.visible = False
        self.unit = None
        self.available_upgrades = []

        # Window dimensions
        self.width = 600
        self.height = 500
        self.x = 0
        self.y = 0

        # Selected upgrade index
        self.selected_index = 0

        # Buttons
        self.confirm_button_rect = None
        self.cancel_button_rect = None
        self.upgrade_rects = []  # Rects for each upgrade option

    def open(self, unit):
        """Open the upgrade window for a unit."""
        from boneglaive.game.upgrades import UpgradeManager

        self.unit = unit
        self.available_upgrades = UpgradeManager.get_available_upgrades(unit)

        if len(self.available_upgrades) == 0:
            return False  # Can't open if no upgrades available

        self.visible = True
        self.selected_index = 0

        return True

    def close(self):
        """Close the upgrade window."""
        self.visible = False
        self.unit = None
        self.available_upgrades = []

    def draw(self, surface: pygame.Surface):
        """Draw the upgrade window."""
        if not self.visible:
            return

        screen_width = surface.get_width()
        screen_height = surface.get_height()

        # Center window
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2

        # Draw semi-transparent background overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # Draw window background
        window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, COLOR_BG, window_rect)
        pygame.draw.rect(surface, COLOR_BORDER, window_rect, 2)

        # Draw title bar
        title_rect = pygame.Rect(self.x, self.y, self.width, 40)
        pygame.draw.rect(surface, COLOR_TITLE_BG, title_rect)

        title_text = f"Upgrade {self.unit.get_display_name()}"
        title_surface = self.font.render(title_text, True, COLOR_TEXT)
        surface.blit(title_surface, (self.x + 20, self.y + 10))

        # Draw upgrade points available
        from boneglaive.game.upgrades import UpgradeManager
        game = self.unit._game  # Access game from unit
        points = game.player1_upgrade_points if self.unit.player == 1 else game.player2_upgrade_points
        points_text = f"Upgrade Points: {points}"
        points_surface = self.small_font.render(points_text, True, COLOR_GOLD)
        surface.blit(points_surface, (self.x + 20, self.y + 50))

        # Draw available upgrades
        self.upgrade_rects = []
        y_offset = 90

        for i, upgrade in enumerate(self.available_upgrades):
            # Upgrade box
            upgrade_rect = pygame.Rect(self.x + 20, self.y + y_offset, self.width - 40, 80)
            self.upgrade_rects.append(upgrade_rect)

            # Highlight if selected
            if i == self.selected_index:
                pygame.draw.rect(surface, COLOR_BUTTON_HOVER, upgrade_rect)
                pygame.draw.rect(surface, COLOR_GREEN, upgrade_rect, 2)
            else:
                pygame.draw.rect(surface, COLOR_BUTTON, upgrade_rect)

            # Draw upgrade name
            name_surface = self.font.render(upgrade['name'], True, COLOR_TEXT)
            surface.blit(name_surface, (upgrade_rect.x + 10, upgrade_rect.y + 10))

            # Draw upgrade description
            desc_surface = self.small_font.render(upgrade['description'], True, COLOR_TEXT_DIM)
            surface.blit(desc_surface, (upgrade_rect.x + 10, upgrade_rect.y + 35))

            # Draw upgrade type badge
            type_text = upgrade['type'].upper()
            type_color = COLOR_GREEN if upgrade['type'] == 'buff' else COLOR_GOLD
            type_surface = self.small_font.render(type_text, True, type_color)
            surface.blit(type_surface, (upgrade_rect.x + 10, upgrade_rect.y + 55))

            y_offset += 90

        # Draw buttons at bottom
        button_y = self.y + self.height - 60

        # Confirm button
        self.confirm_button_rect = pygame.Rect(self.x + 20, button_y, 200, 40)
        pygame.draw.rect(surface, COLOR_GREEN, self.confirm_button_rect)
        confirm_text = self.font.render("CONFIRM", True, COLOR_BG)
        text_rect = confirm_text.get_rect(center=self.confirm_button_rect.center)
        surface.blit(confirm_text, text_rect)

        # Cancel button
        self.cancel_button_rect = pygame.Rect(self.x + self.width - 220, button_y, 200, 40)
        pygame.draw.rect(surface, COLOR_BUTTON, self.cancel_button_rect)
        cancel_text = self.font.render("CANCEL", True, COLOR_TEXT)
        text_rect = cancel_text.get_rect(center=self.cancel_button_rect.center)
        surface.blit(cancel_text, text_rect)

        # Draw instructions
        instructions = "Click an upgrade to select, then CONFIRM. ESC to cancel."
        instr_surface = self.small_font.render(instructions, True, COLOR_TEXT_DIM)
        surface.blit(instr_surface, (self.x + 20, button_y - 25))

    def handle_click(self, pos: tuple) -> Optional[str]:
        """
        Handle mouse click in upgrade window.
        Returns: 'confirm', 'cancel', or None
        """
        if not self.visible:
            return None

        # Check upgrade selection
        for i, rect in enumerate(self.upgrade_rects):
            if rect.collidepoint(pos):
                self.selected_index = i
                return None

        # Check confirm button
        if self.confirm_button_rect and self.confirm_button_rect.collidepoint(pos):
            return 'confirm'

        # Check cancel button
        if self.cancel_button_rect and self.cancel_button_rect.collidepoint(pos):
            return 'cancel'

        return None

    def handle_key(self, key: int) -> Optional[str]:
        """
        Handle keyboard input.
        Returns: 'confirm', 'cancel', or None
        """
        if not self.visible:
            return None

        # ESC to cancel
        if key == pygame.K_ESCAPE:
            return 'cancel'

        # Enter to confirm
        if key == pygame.K_RETURN:
            return 'confirm'

        # Arrow keys to navigate
        if key == pygame.K_UP:
            self.selected_index = max(0, self.selected_index - 1)
        elif key == pygame.K_DOWN:
            self.selected_index = min(len(self.available_upgrades) - 1, self.selected_index + 1)

        return None

    def get_selected_upgrade(self) -> Optional[Dict]:
        """Get the currently selected upgrade."""
        if 0 <= self.selected_index < len(self.available_upgrades):
            return self.available_upgrades[self.selected_index]
        return None
```

**Why**: Provides clean modal window for upgrade selection with mouse and keyboard support.

---

### 4.4 Integrate Upgrade Window into Main Game UI

**File**: `boneglaive/graphical/game_ui.py` (or main pygame UI file)

**Changes**:

1. **Import and Initialize**:
```python
from boneglaive.graphical.ui.upgrade_window import UpgradeWindow

class GameUI:
    def __init__(self, ...):
        # ... existing init ...

        # Create upgrade window
        self.upgrade_window = UpgradeWindow(self.font, self.small_font)
```

2. **Handle UPGRADE Button Click**:
```python
def handle_action_button_click(self, action: str):
    # ... existing action handling ...

    if action == "upgrade":
        if self.selected_unit:
            success = self.upgrade_window.open(self.selected_unit)
            if not success:
                # Show error message (no upgrades available)
                pass
```

3. **Handle Upgrade Window Events**:
```python
def handle_mouse_click(self, pos):
    # Check upgrade window first (if visible)
    if self.upgrade_window.visible:
        result = self.upgrade_window.handle_click(pos)

        if result == 'confirm':
            # Apply selected upgrade
            upgrade = self.upgrade_window.get_selected_upgrade()
            if upgrade:
                game = self.game_adapter.game
                success = game.apply_unit_upgrade(self.upgrade_window.unit, upgrade['skill_name'])
                if success:
                    # Show success message
                    pass
            self.upgrade_window.close()
            return

        elif result == 'cancel':
            self.upgrade_window.close()
            return

        return  # Consumed by upgrade window

    # ... existing click handling ...

def handle_key_press(self, key):
    # Check upgrade window first (if visible)
    if self.upgrade_window.visible:
        result = self.upgrade_window.handle_key(key)

        if result == 'confirm':
            # Apply upgrade (same as click handling above)
            pass
        elif result == 'cancel':
            self.upgrade_window.close()

        return  # Consumed by upgrade window

    # ... existing key handling ...
```

4. **Draw Upgrade Window**:
```python
def draw(self, surface):
    # ... existing draw calls ...

    # Draw upgrade window on top (if visible)
    self.upgrade_window.draw(surface)
```

**Why**: Integrates upgrade window into event flow. Window captures all input when visible.

---

## Phase 5: Expand to All Units

### 5.1 Define Upgrades for Remaining Units

**File**: `boneglaive/game/upgrades.py`

**Add to SKILL_UPGRADES dict**:

```python
"MARROW_CONDENSER": {
    # NOTE: MARROW_CONDENSER already has DOMINION upgrade system
    # May need special handling or integration with existing system
    "Ossify": {
        "name": "Reinforced Ossification",
        "description": "Defense bonus increases from +2 to +3. Duration increases from 2 to 3 turns.",
        "type": "buff",
        "cost": 1
    },
    "Marrow Dike": {
        "name": "Fortified Dike",
        "description": "Wall HP increases from 1/2 to 2/3. Pull damage increases from 3 to 4.",
        "type": "buff",
        "cost": 1
    },
    "Bone Tithe": {
        "name": "Marrow Drain",
        "description": "Damage increases from 1 to 2. HP gain per enemy increases from 1/2 to 2/3.",
        "type": "buff",
        "cost": 1
    },
    "Dominion": {
        "name": "Apex Dominion",
        "description": "Gain stat bonuses at 2 kills instead of 3.",
        "type": "buff",
        "cost": 1
    }
},

"FOWL_CONTRIVANCE": {
    # TODO: Add FOWL_CONTRIVANCE skill upgrades
    # Skills: Divebomb, Perch, Aerial Bombardment, Thermogenic (passive)
},

"GAS_MACHINIST": {
    # TODO: Add GAS_MACHINIST skill upgrades
    # Skills: Deploy Vapor, Ignite, Pressurize, Caustic Presence (passive)
},

"DELPHIC_APPRAISER": {
    # TODO: Add DELPHIC_APPRAISER skill upgrades
    # Skills: Market Futures, Auction Curse, Investment, Anchor (passive)
},

"INTERFERER": {
    # TODO: Add INTERFERER skill upgrades
    # Skills: Scalar Node, Neural Shunt, Carrier Rave, Radiation (passive)
},

"DERELICTIONIST": {
    # TODO: Add DERELICTIONIST skill upgrades
    # Skills: Severance, Partition, Isolation, Dereliction (passive)
},

"POTPOURRIST": {
    # TODO: Add POTPOURRIST skill upgrades
    # Skills: Infusion, Demilune, Geas, Aromatic (passive)
}
```

**Action Items**:
1. Research each unit's skills (read skill files)
2. Design meaningful upgrades for each (damage, range, cooldown, duration, special effects)
3. Consider side-grades for already-strong abilities
4. Balance upgrade power (should feel impactful but not game-breaking)

---

### 5.2 Update Skill Files for All Units

**Files**:
- `boneglaive/game/skills/marrow_condenser.py`
- `boneglaive/game/skills/fowl_contrivance.py`
- `boneglaive/game/skills/gas_machinist.py`
- `boneglaive/game/skills/delphic_appraiser.py`
- `boneglaive/game/skills/interferer.py`
- `boneglaive/game/skills/derelictionist.py`
- `boneglaive/game/skills/potpourrist.py`

**Apply same pattern as Phase 2**: Add upgrade check at start of `execute()` or `apply_passive()`, modify behavior based on `self.upgraded` flag.

---

### 5.3 Balance Testing

**Test Scenarios**:
1. **Early upgrade impact**: Does upgrading at 2 GP feel powerful enough?
2. **Late upgrade impact**: Does upgrading at 4 GP swing the game too much?
3. **Banking strategy**: Is saving points for 4 GP viable, or better to spend at 2 GP?
4. **Unit viability**: Do previously weak units become more viable with upgrades?
5. **Counterplay**: Can you tell which enemy skills are upgraded and adapt?

**Metrics to Track**:
- Win rate when upgrading early vs. banking
- Most popular upgrades per unit
- Games won/lost before 4 GP threshold (does upgrade system matter?)

---

### 5.4 Add Upgrade Info to Help System

**Files**:
- `boneglaive/ui/ui_components.py` (ASCII help)
- `boneglaive/graphical/ui/setup_unit_help.py` (graphical help)

**Changes**:

Add upgrade descriptions to each unit's help page:

```python
# In UnitHelpComponent._load_unit_help_data()
{
    'skills': [
        {
            'name': 'JUDGEMENT (Active) [Key: J]',
            'description': '...',
            'details': ['...'],
            'upgrade': {  # NEW
                'name': 'Divine Judgement',
                'description': 'Damage increases from 4/8 to 6/12. Range increases from 4 to 5.',
                'cost': 1
            }
        }
    ]
}
```

Show upgrade info in help display (maybe with a special icon or section).

---

### 5.5 Visual Effects for Upgrades (Optional Polish)

**Graphical Mode**:
- Particle effect when upgrade applied (sparkles, glow)
- Unit sprite tint/outline when upgraded
- Skill icon badge showing "+" or star

**ASCII Mode**:
- Flash unit tile when upgrade applied
- Add indicator symbol next to upgraded units (maybe asterisk "*")

---

## Edge Cases & Special Considerations

### Respawn Handling

**Issue**: When unit dies and respawns, should upgrades persist?

**Decision**: YES - upgrades persist through respawn.

**Implementation**:
- Store `upgraded_skills` set on Unit instance
- When creating respawned unit, copy `upgraded_skills` from DeadUnit:

```python
# In respawn logic (wherever units are respawned)
def respawn_unit(self, dead_unit, y, x):
    new_unit = Unit(dead_unit.unit_type, dead_unit.player, y, x)

    # Copy upgrades from dead unit
    if hasattr(dead_unit, 'upgraded_skills'):
        new_unit.upgraded_skills = dead_unit.upgraded_skills.copy()

    # ... rest of respawn logic
```

**Why**: Maintains upgrade investment. Players shouldn't lose upgrades on death (they already lose time via respawn timer).

---

### DOMINION Integration

**Issue**: MARROW_CONDENSER already has DOMINION upgrade system that auto-upgrades skills.

**Options**:

**Option A**: Keep DOMINION separate, player upgrades are additional
- DOMINION still auto-upgrades at certain kill counts
- Player can also manually upgrade with upgrade points
- Skills can be "double upgraded" (DOMINION + manual)

**Option B**: Replace DOMINION with manual upgrade system
- Remove auto-upgrade from DOMINION
- MARROW_CONDENSER uses same upgrade system as other units
- DOMINION just gives stat bonuses, not skill upgrades

**Recommendation**: **Option A** - Keep DOMINION unique. It's a cool mechanic that defines MARROW_CONDENSER. Manual upgrades add on top of DOMINION.

**Implementation**:
```python
# In marrow_condenser skill execute()
def execute(self, user, target_pos, game, ui=None):
    # Check both DOMINION and manual upgrades
    dominion_upgraded = hasattr(user.passive_skill, 'marrow_dike_upgraded') and user.passive_skill.marrow_dike_upgraded
    manual_upgraded = hasattr(user, 'upgraded_skills') and 'Marrow Dike' in user.upgraded_skills

    # Apply both upgrade effects (stack them)
    if dominion_upgraded:
        # DOMINION upgrade effects
        pass

    if manual_upgraded:
        # Manual upgrade effects
        pass
```

---

### Side-Grade Implementation

**Issue**: Side-grades change behavior fundamentally (e.g., GRAYMAN phase shift through terrain).

**Implementation Notes**:
- Some side-grades require changes to core systems (movement validation, terrain checks)
- Start with simple side-grades (stat trades: +damage -range, etc.)
- Complex side-grades (phase shift, area effects) can be Phase 6 (post-launch polish)

**Example Simple Side-Grade**:
```python
"GLAIVEMAN": {
    "Judgement": {
        "name": "Rapid Judgement",
        "description": "Cooldown reduces from 4 to 2, but damage decreases from 8 to 6.",
        "type": "sidegrade",
        "cost": 1
    }
}
```

---

### Multiplayer Sync

**Issue**: In network multiplayer, upgrades need to sync between clients.

**Implementation**:
- Upgrade application should be part of game state
- Network protocol needs to transmit upgrade events
- Both clients apply same upgrade to same unit

**Files to Check**:
- `boneglaive/networking/` (if exists)
- Look for existing network sync patterns (unit moves, attacks)
- Apply same pattern to upgrades

**Note**: Defer network sync to Phase 6 if multiplayer isn't currently functional.

---

### DLC Unit Support

**Confirmation**: DLC units (PELOTARI, future units) will have upgrades too.

**Implementation**:
- DLC units should register their upgrades when loaded
- Extend `SKILL_UPGRADES` dict dynamically:

```python
# In DLC loading code
def register_dlc_upgrades(unit_type_name, upgrades):
    """Register upgrades for a DLC unit."""
    from boneglaive.game.upgrades import SKILL_UPGRADES
    SKILL_UPGRADES[unit_type_name] = upgrades

# In PELOTARI DLC
register_dlc_upgrades("PELOTARI", {
    "Forehand": { ... },
    "Backhand": { ... },
    # etc.
})
```

**Why**: Keeps upgrade system extensible for future content.

---

## Testing Checklist

### Phase 1 Tests (Backend)
- [ ] Upgrade points awarded at 2 GP threshold
- [ ] Upgrade points awarded at 4 GP threshold
- [ ] Upgrade points not double-awarded if GP fluctuates
- [ ] Upgrade points correctly tracked per player
- [ ] UpgradeManager.get_available_upgrades() returns correct upgrades
- [ ] UpgradeManager.apply_upgrade() deducts points correctly
- [ ] UpgradeManager.apply_upgrade() prevents re-upgrading same skill
- [ ] Upgrade log messages appear when upgrades applied

### Phase 2 Tests (Skills)
- [ ] GLAIVEMAN Judgement damage increases when upgraded
- [ ] GLAIVEMAN Vault range increases when upgraded
- [ ] MANDIBLE_FOREMAN Expedite damage increases when upgraded
- [ ] GRAYMAN Delta Config cooldown reduces when upgraded
- [ ] Upgraded skills show visual/log differences (if applicable)

### Phase 3 Tests (ASCII UI)
- [ ] Upgrade points display in status bar
- [ ] U key opens upgrade menu for selected unit
- [ ] Upgrade menu shows available upgrades
- [ ] Hotkeys (Q/W/E/R) select and apply upgrades
- [ ] ESC closes upgrade menu
- [ ] Menu shows error if no upgrades available
- [ ] Menu shows error if no upgrade points available

### Phase 4 Tests (Graphical UI)
- [ ] Upgrade points display in top bar
- [ ] UPGRADE button enabled when upgrades available
- [ ] UPGRADE button disabled when no upgrades/points
- [ ] Clicking UPGRADE button opens upgrade window
- [ ] Upgrade window shows available upgrades
- [ ] Clicking upgrade selects it (highlight)
- [ ] CONFIRM applies selected upgrade
- [ ] CANCEL closes window without applying
- [ ] ESC closes window without applying
- [ ] Arrow keys navigate upgrades

### Phase 5 Tests (All Units)
- [ ] All 10 base units have upgrades defined
- [ ] All upgrade effects implemented in skill files
- [ ] Balance testing: upgrades feel impactful but not OP
- [ ] Help pages show upgrade information
- [ ] DLC units (PELOTARI) have upgrades

### Edge Case Tests
- [ ] Respawned units retain upgrades
- [ ] DOMINION upgrades and manual upgrades coexist
- [ ] Upgrades persist across turns
- [ ] Banking upgrade points works correctly
- [ ] Can't upgrade opponent's units
- [ ] Can't upgrade when not your turn

---

## File Summary

### New Files to Create
1. `boneglaive/game/upgrades.py` - Upgrade registry and manager
2. `boneglaive/graphical/ui/upgrade_window.py` - Graphical upgrade UI

### Files to Modify
1. `boneglaive/game/engine.py` - Add upgrade point tracking and award logic
2. `boneglaive/game/units.py` - Add `upgraded_skills` attribute
3. `boneglaive/game/skills/glaiveman.py` - Add upgrade checks to skills
4. `boneglaive/game/skills/mandible_foreman.py` - Add upgrade checks to skills
5. `boneglaive/game/skills/grayman.py` - Add upgrade checks to skills
6. `boneglaive/game/skills/marrow_condenser.py` - Add upgrade checks to skills
7. `boneglaive/game/skills/fowl_contrivance.py` - Add upgrade checks to skills
8. `boneglaive/game/skills/gas_machinist.py` - Add upgrade checks to skills
9. `boneglaive/game/skills/delphic_appraiser.py` - Add upgrade checks to skills
10. `boneglaive/game/skills/interferer.py` - Add upgrade checks to skills
11. `boneglaive/game/skills/derelictionist.py` - Add upgrade checks to skills
12. `boneglaive/game/skills/potpourrist.py` - Add upgrade checks to skills
13. `boneglaive/ui/ui_components.py` - Add UpgradeMenuComponent, update status display
14. `boneglaive/ui/game_ui.py` - Integrate upgrade menu, add U hotkey
15. `boneglaive/graphical/ui/top_bar.py` - Display upgrade points
16. `boneglaive/graphical/ui/action_menu.py` - Enable UPGRADE button
17. `boneglaive/graphical/game_ui.py` - Integrate upgrade window

---

## Timeline Estimate

**Phase 1 (Backend)**: 2-3 hours
- Straightforward data structure and logic additions

**Phase 2 (Test Units)**: 2-3 hours
- Update 3 units' skills, test manually

**Phase 3 (ASCII UI)**: 3-4 hours
- New UI component, hotkey handling, integration

**Phase 4 (Graphical UI)**: 4-5 hours
- New window component, click handling, integration

**Phase 5 (All Units)**: 6-8 hours
- Design upgrades for 7 remaining units
- Update all skill files
- Balance testing

**Total**: ~17-23 hours (2-3 full development days)

---

## Next Steps

When ready to implement:

1. **Start with Phase 1** - Get backend working first
2. **Manual testing** - Use Python REPL to verify upgrade logic
3. **Phase 2 with 2-3 units** - Prove the concept works
4. **Choose UI path** (ASCII first or graphical first)
5. **Iterate on balance** - Play full matches, adjust upgrade power

---

## Notes

- This system mirrors DOMINION's pattern (already proven to work)
- UPGRADE button already exists in action menu (someone planned ahead!)
- Per-unit storage keeps things simple and flexible
- Banking points adds strategic depth without complexity
- Side-grades keep strong units interesting (GRAYMAN, STASIALITY)
- DLC extensibility built-in from the start

---

## Open Questions

1. **Should upgrades be visible to opponent?**
   - Currently: Log message only ("Player 1 upgraded GLAIVEMAN's Judgement")
   - Alternative: Show icon/indicator on upgraded units (more info, less mystery)

2. **Should some units have more upgrades than others?**
   - Currently: All units have 4 upgrades (3 skills + 1 passive)
   - Alternative: Complex units have more options (5-6 upgrades)

3. **Should upgrade costs vary?**
   - Currently: All upgrades cost 1 point
   - Alternative: Powerful upgrades cost 2 points (spend both at once)

4. **Should there be upgrade trees?**
   - Currently: All upgrades available at once
   - Alternative: Some upgrades unlock other upgrades (tree structure)

**Recommendation**: Start simple (all current assumptions), add complexity in Phase 6 if needed.
