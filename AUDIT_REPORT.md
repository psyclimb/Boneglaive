# Boneglaive Code Audit Report

**Date:** 2026-06-13
**Branch:** v1.3
**Standard:** CODE_STANDARD.md (all 10 sections)
**Scope:** All Python files under `boneglaive/`, `run_graphical.py`; excludes `tests/`
**Status:** All 20 findings resolved.

---

## Summary

| Section | Findings | Status |
|---------|----------|--------|
| 1. Dead Code | 4 | FIXED |
| 2. Single Responsibility | 0 | Clean |
| 3. Data Flow | 1 | FIXED |
| 4. Consistency | 2 | FIXED |
| 5. Architecture Boundaries | 2 | FIXED |
| 6. No Overengineering | 0 | Clean |
| 7. Constants & Magic Numbers | 5 | FIXED |
| 8. Naming | 0 | Clean |
| 9. Docstrings & Comments | 4 | FIXED |
| 10. Version & Config Hygiene | 2 | FIXED |

---

## Section 1 — Dead Code

### 1.1 Commented-out code in ui_adapter.py (FIXED)
Removed commented-out `self._render_and_wait(0.3)` and its comment at `boneglaive/graphical/ui_adapter.py:78-79`.

### 1.2 Deprecated color constants (FIXED)
Removed unused `COLOR_TEXT_COMBAT`, `COLOR_TEXT_ABILITY`, `COLOR_TEXT_MOVEMENT` from both `boneglaive/graphical/ui/combat_log.py` and `boneglaive/graphical/ui/message_log_window.py`.

### 1.3 Dead methods in coordinates.py (FIXED)
Fixed `Position.distance_to()` to use Chebyshev distance and `Position.is_adjacent()` to use `<= 1` threshold. Methods are now correct if called in the future. (See also 4.1.)

### 1.4 Stale deprecation comment in engine.py (FIXED)
Changed comment on `dominion_permanent_attack` from "old system - deprecated" to "Retained for save compatibility".

---

## Section 3 — Data Flow

### 3.1 Game engine spawns graphical animations directly (FIXED)
Replaced direct `PartitionHitAnimation` import/spawn in `boneglaive/game/units.py` with a `partition_hit_for_animation` flag. The graphical layer (`game_state.py`) now detects the flag and dispatches an `AnimationEvent`, which `renderer.py` handles. Text-mode animation preserved inline with a `hasattr(renderer, 'camera')` guard.

---

## Section 4 — Consistency

### 4.1 Manhattan distance in Position.distance_to() (FIXED)
Changed from `abs(dy) + abs(dx)` (Manhattan) to `max(abs(dy), abs(dx))` (Chebyshev). Updated `is_adjacent()` threshold from `<= 2` to `<= 1`.

### 4.2 Coordinate order (x, y) in game_state.py (FIXED)
Added explicit comment `# Screen coords (x, y), not game coords (y, x)` on `last_position` initialization and clarified the inline comment at the usage site to document this is a deliberate graphical-layer convention.

---

## Section 5 — Architecture Boundaries

### 5.1 Game engine imports from graphical layer (FIXED)
Removed `from boneglaive.graphical.animations import PartitionHitAnimation` from `boneglaive/game/units.py`. Game engine now sets a flag; graphical renderer detects and spawns the animation. See 3.1.

### 5.2 Game engine imports from curses UI layer (FIXED)
Moved `unit_help_data.py` from `boneglaive/game/` to `boneglaive/utils/` (shared layer). Updated import paths in `boneglaive/graphical/ui/help_page.py` and `boneglaive/graphical/ui/setup_unit_help.py`.

---

## Section 7 — Constants & Magic Numbers

### 7.1 MAX_UNITS not used in engine.py (FIXED)
`engine.py` now imports and uses `MAX_UNITS` from `constants.py` for `setup_units_remaining` and zone size checks.

### 7.2 Respawn timer hardcoded (FIXED)
Added `RESPAWN_TIMER = 3` to `constants.py`. `engine.py` `DeadUnit.__init__` now uses the constant.

### 7.3 Upgrade point thresholds hardcoded (FIXED)
Added `UPGRADE_POINT_THRESHOLDS = [2, 4, 6]` to `constants.py`. `engine.py` now uses the constant.

### 7.4 Setup minimum distance hardcoded (FIXED)
Added `SETUP_MIN_DISTANCE = 3` to `constants.py`. `engine.py` now uses the constant.

### 7.5 Invulnerability PRT hardcoded as 999 (FIXED)
Added `INVULNERABLE_PRT = 999` to `constants.py`. Updated all usages in `units.py` (Heinous Vapor init, partition dissociation) and `skills/landscaper.py` (Topiary Breath).

---

## Section 9 — Docstrings & Comments

### 9.1 Missing module docstring in game_ui.py (FIXED)
Added `"""Game UI — curses-based interactive game interface."""` at top of `boneglaive/ui/game_ui.py`.

### 9.2 Stale "deprecated" comments on color constants (FIXED)
Resolved by removing the unused constants entirely (see 1.2).

### 9.3 Restatement comments in units.py (FIXED)
Removed ~60 inline comments in the status effect initialization block (lines 86-197) that merely restated variable names. Kept only comments that explain *why* (e.g., player 2 move bonus rationale, doppelganger decrement timing, Severance mechanics).

### 9.4 Stale deprecation comment in engine.py (FIXED)
Resolved — see 1.4.

---

## Section 10 — Version & Config Hygiene

### 10.1 "Beta Release" label removed (FIXED)
Removed stale "Beta Release" line from text-mode about screen in `boneglaive/ui/menu_ui.py`.

### 10.2 Copyright year updated (FIXED)
Changed "2025" to "2026" in text-mode about screen in `boneglaive/ui/menu_ui.py` to match all other copyright notices.

---

## Files Modified

| File | Changes |
|------|---------|
| `boneglaive/utils/constants.py` | Added RESPAWN_TIMER, UPGRADE_POINT_THRESHOLDS, SETUP_MIN_DISTANCE, INVULNERABLE_PRT |
| `boneglaive/game/engine.py` | Use constants for magic numbers; fix stale comment |
| `boneglaive/game/units.py` | Use INVULNERABLE_PRT; replace animation import with flag; strip restatement comments |
| `boneglaive/game/skills/landscaper.py` | Use INVULNERABLE_PRT for topiary PRT |
| `boneglaive/graphical/game_state.py` | Detect partition_hit_for_animation flag; clarify coordinate comments |
| `boneglaive/graphical/renderer.py` | Handle "partition_hit" animation event |
| `boneglaive/graphical/ui_adapter.py` | Remove commented-out code |
| `boneglaive/graphical/ui/combat_log.py` | Remove unused deprecated color constants |
| `boneglaive/graphical/ui/message_log_window.py` | Remove unused deprecated color constants |
| `boneglaive/graphical/ui/help_page.py` | Update import path for unit_help_data |
| `boneglaive/graphical/ui/setup_unit_help.py` | Update import path for unit_help_data |
| `boneglaive/ui/game_ui.py` | Add module docstring |
| `boneglaive/ui/menu_ui.py` | Remove "Beta Release", fix copyright year |
| `boneglaive/utils/coordinates.py` | Fix distance_to (Chebyshev), fix is_adjacent threshold |
| `boneglaive/utils/unit_help_data.py` | Moved from boneglaive/game/ (boundary fix) |
