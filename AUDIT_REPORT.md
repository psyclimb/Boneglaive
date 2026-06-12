# Boneglaive Code Audit Report

Audited against `CODE_STANDARD.md` on 2026-06-12 (branch: v1.3).
Every finding below was manually verified against source. Excludes items that would
require extreme overhaul, major refactors, or risk breaking existing functionality.

Previously-known issues (from `v1.3_changes.md` "Remaining Audit Findings") are
not repeated here unless new context was found.

---

## 1. Dead Code

### Stale XP / Leveling System
The entire XP system is non-functional. Constants are set to zero with "temporarily"
comments but are still referenced in live code paths.

| File | Line | Issue |
|------|------|-------|
| `boneglaive/utils/constants.py` | 12-14 | `XP_KILL_REWARD = 0`, `XP_DAMAGE_FACTOR = 0` with "temporarily set to 0 for testing" |
| `boneglaive/utils/constants.py` | 11 | `MAX_LEVEL = 5` — unused in practice (XP never accumulates) |
| `boneglaive/utils/constants.py` | 17-23 | `XP_PER_LEVEL` dict — never meaningfully consulted |
| `boneglaive/game/engine.py` | 3992-3997 | Imports and applies `XP_DAMAGE_FACTOR` and `XP_KILL_REWARD` (always 0) |
| `boneglaive/game/units.py` | 6, 632 | Imports `MAX_LEVEL`, `XP_PER_LEVEL`; `gain_xp()` exists but never triggers level-up |
| `boneglaive/graphical/ui/unit_info.py` | 341-342 | Imports `XP_PER_LEVEL` for XP bar display (always empty) |

### Unused Functions
| File | Line | Issue |
|------|------|-------|
| `boneglaive/utils/platform_compat.py` | 46 | `get_config_directory()` has zero callers; duplicated by `paths.py:user_config_dir()` |

### Dead Blocks in engine.py
| Line | Issue |
|------|-------|
| 4660-4664 | Loop over all units with body `pass` — comment says passives moved elsewhere |
| 6568-6569 | `if affected_units: pass` — dead conditional after summary message removal |

### Redundant Inline Imports
| File | Lines | Issue |
|------|-------|-------|
| `boneglaive/game/engine.py` | 2323, 3069, 3402, 4889 | `import time` repeated inline when already imported at line 7 |

### Commented-Out Code
| File | Line | Issue |
|------|------|-------|
| `boneglaive/graphical/ui_adapter.py` | 179 | `# self._render_and_wait(0.4)  # Removed for smooth gameplay` |
| `boneglaive/graphical/assets/__init__.py` | 7-8 | `# from .asset_manager import AssetManager` / `# from .sprite_loader import SpriteLoader` |

### Tombstone "Removed" Comments
These comments document what was deleted — the standard says to delete them (git has history).

| File | Line(s) | Comment |
|------|---------|---------|
| `boneglaive/utils/input_handler.py` | 84 | "removed Vim-style keys" |
| `boneglaive/utils/input_handler.py` | 106 | "Removed test mode key ('e')" |
| `boneglaive/utils/input_handler.py` | 111 | "Removed debug context and keys" |
| `boneglaive/utils/input_handler.py` | 176 | "removed debug" |
| `boneglaive/ui/ui_components.py` | 186 | "Removed colored text handling methods" |
| `boneglaive/game/engine.py` | 4737 | "Removed healing effect for upgraded Marrow Dikes" |
| `boneglaive/game/skills/marrow_condenser.py` | 248 | "Removed prevention check" |
| `boneglaive/game/skills/fowl_contrivance.py` | 1230 | "Removed extraneous fragmentation message" |
| `boneglaive/game/map.py` | 1028 | "Removed lime_foyer_arena map reference" |
| `boneglaive/graphical/animations/glaiveman.py` | 3025-3026 | "Removed: Impact sound / Impact flashes" |
| `boneglaive/graphical/animations/glaiveman.py` | 3060 | "Removed: Impact flash updates" |
| `boneglaive/graphical/animations/glaiveman.py` | 3103 | "Removed: Impact flashes drawing" |

---

## 2. Leftover Scaffolding (TODO / FIXME Stubs)

| File | Line | Stub |
|------|------|------|
| `boneglaive/ai/skill_simulator.py` | 204 | `# TODO: Handle AOE skills by checking nearby units` |
| `boneglaive/graphical/assets/__init__.py` | 6 | `# TODO: Add asset management classes` |
| `boneglaive/graphical/ui/loto_system.py` | 87 | `# TODO: Add Viseroy skill blocking when implemented` |
| `boneglaive/graphical/game_state.py` | 531 | `source_unit=None,  # TODO: Track damage source` |
| `boneglaive/graphical/game_state.py` | 815 | `# FIXME: move_to_grid calculates target position without offset` |
| `boneglaive/graphical/game_state.py` | 1519 | `# TODO: Execute skill through game logic` |
| `boneglaive/graphical/game_state.py` | 1539 | `# TODO: Execute move through game logic` |
| `boneglaive/graphical/game_state.py` | 1546 | `# TODO: End turn in game logic` |
| `boneglaive/graphical/game_state.py` | 1569 | `# TODO: Add more state as needed` |
| `boneglaive/graphical/game_state.py` | 1583 | `# TODO: Query game logic for valid targets` |
| `boneglaive/graphical/game_state.py` | 1590 | `# TODO: Query game logic` |
| `boneglaive/graphical/game_state.py` | 1596 | `# TODO: Query game logic` |
| `boneglaive/graphical/renderer.py` | 1260 | `# TODO: Execute skill on target` |
| `boneglaive/graphical/renderer.py` | 1659 | `return unit.name  # TODO: Use proper unit ID` |
| `boneglaive/graphical/animations/animation_factory.py` | 260 | `# Check if caster has infusion buff (TODO: implement check)` |
| `boneglaive/graphical/animations/animation_factory.py` | 407 | `direction=0  # TODO: determine direction based on caster facing` |
| `boneglaive/ui/pygame_game_ui.py` | 225 | `# TODO: Implement settings menu` |

---

## 3. Stale / Incorrect Comments

| File | Line | Issue |
|------|------|-------|
| `boneglaive/ai/__init__.py` | 4 | Docstring says "placeholder for future AI implementation" — AI is fully implemented |
| `boneglaive/utils/config.py` | 20 | `GameMode` docstring says `"""Network mode options."""` — should say "Game mode options" |
| `boneglaive/utils/config.py` | 39 | Section header `# Network settings` — should say "Game mode settings" |
| `boneglaive/main.py` | 55 | Comment `# Network mode` — should say "Game mode" |
| `boneglaive/game/multiplayer_manager.py` | 65 | Error string `f"Unknown network mode: {game_mode}"` — should say "game mode" |
| `boneglaive/graphical/renderer.py` | 5281 | Comment says "based on network mode" |
| `setup.py` | 3 | Docstring says "Boneglaive2 Setup Script" — project is "Boneglaive" |

---

## 4. Missing Module Docstrings

The standard requires a one-line module docstring at the top of every `.py` file.

| File | Issue |
|------|-------|
| `boneglaive/__init__.py` | Has `# Boneglaive package` comment, not a docstring |
| `boneglaive/game/__init__.py` | Empty file |
| `boneglaive/ui/__init__.py` | Only imports, no docstring |
| `boneglaive/utils/__init__.py` | Empty file |
| `boneglaive/utils/constants.py` | No docstring |
| `boneglaive/utils/debug.py` | No docstring |
| `boneglaive/game/engine.py` | No docstring |

---

## 5. Version & Config Hygiene

### Version String Drift
`__version__` in `boneglaive/__init__.py` is the single source of truth per the standard,
but multiple files hardcode the version independently.

| File | Line | Value | Issue |
|------|------|-------|-------|
| `boneglaive/__init__.py` | 2 | `"1.2"` | Source of truth — needs bump to 1.3 when releasing |
| `setup.py` | 28 | `"1.2"` | Hardcoded; should `from boneglaive import __version__` |
| `boneglaive/graphical/ui/about_screen.py` | 58 | `"Boneglaive v1.2"` | Hardcoded string |
| `boneglaive/graphical/ui/main_menu.py` | 118 | `"v1.2"` | Hardcoded string |
| `boneglaive/ui/menu_ui.py` | 248 | `"Boneglaive v1.2"` | Hardcoded string |
| `boneglaive/ui/menu_ui.py` | 285 | `"v1.2"` | Hardcoded check |
| `boneglaive/ui/menu_ui.py` | 561 | `"v1.2"` | Hardcoded subtitle |

All UI version strings should reference `__version__` so a single bump propagates everywhere.

---

## 6. Naming & Consistency

| File | Line | Issue |
|------|------|-------|
| `boneglaive/game/player_profile.py` | 38 | `Dict[str, any]` — lowercase `any` should be `Any` from typing |
| `boneglaive/game/player_profile.py` | 178 | `list[str]` return type — inconsistent with `List[str]` used elsewhere in file |

### Duplicate Sound Registry Keys
| File | Lines | Issue |
|------|-------|-------|
| `boneglaive/graphical/sound_registry.py` | 43-44 | `"GRAE_EXCHANGE"` and `"GRÆ_EXCHANGE"` both map to `"grae_exchange"` — pick one canonical key |
| `boneglaive/graphical/sound_registry.py` | 80-82 | Three keys for the same sound: `"DEFT(?) REROLL"`, `"DEFT(?)_REROLL"`, `"DEFT_REROLL"` — consolidate |

---

## 7. Architecture Boundaries (Out-of-Scope, Noted for Awareness)

The standard says the game engine (`boneglaive/game/`) should be headless — no pygame,
no curses, no rendering. In practice, `engine.py` and nearly every skill file import
`curses` for inline text-mode animations (40+ total import sites across 14 files).

This is the most significant structural deviation from the standard, but fixing it would
require decoupling the entire text-mode rendering pipeline from game logic — a major
refactor well beyond the scope of a cleanup pass.

**Affected files**: `engine.py`, `units.py`, and all 12 skill files in `boneglaive/game/skills/`.

---

## Summary

| Category | Count | Severity |
|----------|-------|----------|
| Dead code (stale XP system, unused functions, dead blocks) | 6 items | Medium |
| Commented-out code & tombstone comments | 14 items | Low |
| TODO/FIXME stubs | 17 items | Low |
| Stale/incorrect comments | 7 items | Low |
| Missing module docstrings | 7 files | Low |
| Version string drift | 7 locations | Medium |
| Naming/consistency | 6 items | Low |
| Architecture boundaries (out-of-scope) | 14 files | High (structural) |

Total actionable findings: **64 items** across ~30 files.
Most are low-severity cleanup that can be addressed incrementally without risk.
