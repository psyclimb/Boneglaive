# Dead / Orphaned Code Audit — Boneglaive

> **STATUS: EXECUTED 2026-06-24** — commit `a5b95d0` on `v1.4` (local only, not pushed).
> ~5,300 net lines removed across 74 files (8 whole files deleted). Behavior-preserving:
> test_headless_combat / test_ordnance_graft / test_ordnance_graft_ai all PASS, headless boot
> exit 124, pyflakes undefined-name count unchanged (only the known glaiveman false positive).
> **Intentionally left** (low value / higher risk for one squashed commit): write-only skill attrs
> (`fire_source`, `OssifySkill.upgraded`, `FragcrestSkill.upgraded_*`, mandible `effect_symbol`),
> unused UI theme constants (`MINIMIZED_*`, `COLOR_VICTORY/DEFEAT/OVERLAY/TEXT_DIM/BG_DARK`,
> `LINE_SPACING`), the `__init__.py` re-export "unused imports" (load-bearing), `handle_player_action`
> unused branches, `DeadUnit.dominion_permanent_attack` (save-compat), `is_skill_upgraded` AI branches,
> and the ~81 pyflakes unused-locals. The latent bugs in §10 were NOT touched (out of scope).

**Date:** 2026-06-24 · **Branch:** v1.4 · **Scope:** entire `boneglaive/` package (100 files, ~86K LOC) + top-level scripts

**Method.** Seven parallel per-area audits (each symbol grep-verified across `boneglaive/` + `tests/` + `run_graphical.py`), cross-checked against two static tools — `pyflakes` (unused imports/locals) and `vulture` (unused functions/classes/attrs) — and every high-impact claim independently re-verified by hand. Dynamic-dispatch traps were explicitly accounted for: string-keyed skill/animation/sound dispatch, `unit.type ==` chains, `getattr`, EventManager subscriptions, callback assignment, same-name methods on different classes, and renderer/AI reads of `Unit` fields.

**Confidence legend:** **HIGH** = verified zero live references / provably unreachable. **MED** = dead unless a dynamic path was missed, or dead-by-transitivity. **LOW** = suspicious / judgment call.

---

## TL;DR — what to delete, biggest first

| # | Item | Approx. LOC | Conf |
|---|---|---|---|
| 1 | `ai/skill_simulator.py` — whole module (built, never invoked) | ~356 | HIGH |
| 2 | `ai/pathfinding.py` — whole module (built, never invoked) | ~383 | HIGH |
| 3 | `utils/event_system.py` — ~95% dead (no `.publish()` exists anywhere) | ~200 | HIGH |
| 4 | `graphical/sound_registry.py` — `MULTI_EVENT_SOUNDS` + 3 getter/table pairs | ~330 | HIGH |
| 5 | `game/recruitment.py` — 4 classes + global, only `RECRUITMENT_ORDER` is live | ~220 | HIGH |
| 6 | `game/multiplayer_manager.py` — whole module (never imported) | ~205 | HIGH |
| 7 | `graphical/ui/panel_decorations.py` — whole module (never wired in) | 266 | HIGH |
| 8 | **Backhand mechanic** — orphaned status effect from a removed unit, spans 5 files | ~80 | HIGH |
| 9 | `game/map.py` — `LimeFoyerMap` class + lighting subsystem + `to_json` | ~180 | HIGH |
| 10 | `graphical/renderer.py` — `draw_grid_old`, `setup_demo_scene`, dead `main()` | ~150 | HIGH |
| 11 | `graphical/ui/animated_background.py` — whole module (imported, never instantiated) | ~160 | HIGH |
| 12 | `game/animations.py` — whole module (duplicate `get_line`, never imported) | 23 | HIGH |
| 13 | `utils/animation_helpers.py` — whole module (never imported) | 29 | HIGH |
| — | ~12 dead engine/units methods, dead camera/sound_manager/game_state methods | — | HIGH |
| — | ~165 unused imports + ~85 unused locals (pyflakes) | — | HIGH |

**Rough total: ~3,000+ lines of removable dead code**, dominated by three never-invoked subsystems (AI simulator, AI pathfinder, event bus) and several mechanics/units that were removed without full cleanup.

There is a clear through-line: **a melee "matador/swordsman" unit was deleted** (leaving the Backhand effect + Matador/Poach/Backhand animations + phantom factory branches), and **the Saft-E-Gas targeting-protection sub-feature, the tile-lighting system, the network-multiplayer scaffolding, and the EventManager pub/sub bus were all abandoned mid-wiring**. The ASCII-removal cleanup (already done) was thorough; this is the *next* layer of cruft underneath it.

---

## 1. Whole-module orphans (delete the file)

### `boneglaive/ai/skill_simulator.py` — ~356 lines — **HIGH**
`SkillSimulator` is constructed as `self.skill_sim` in `smart_ai.py:40` and **never used again** — anywhere in the tree. Its sole public entry `score_skill_action` (:319) has zero callers; everything else (`simulate_skill`, `_analyze_skill`, `_estimate_skill_damage/_healing`, `_get_affected_units`, `_evaluate_repositioning`, `_evaluate_status_effects`, `_calculate_total_value`, `SkillOutcome`) is reachable only through it. The AI scores skills via `TacticalEvaluator`, which superseded this keyword-heuristic predictor.

### `boneglaive/ai/pathfinding.py` — ~383 lines — **HIGH**
`PathfindingEngine` is constructed as `self.pathfinder` in `smart_ai.py:41` and **never used again**. All three public methods (`find_path`, `find_best_approach_position`, `find_retreat_position`) have zero callers; the `A*` internals + `PathNode` are reachable only through them. The AI does its own reachable-tile/approach logic inside `TacticalEvaluator`.

> **Cleanup for #1 & #2:** also remove `smart_ai.py:12-13` (imports) and `:40-41` (the two `self.skill_sim`/`self.pathfinder` constructions). They exist solely to build never-used objects.

### `boneglaive/game/multiplayer_manager.py` — ~205 lines — **HIGH**
`MultiplayerManager` (the whole class + all 11 methods + module imports) is **never imported or instantiated** anywhere. Only two stale *comments* in `engine.py:4432` and `ai_interface.py:18` mention "the multiplayer manager." The engine reimplements all player-switching inline (`engine.py:4433-4441`), and the renderer drives turn flow directly. Vestige of the curses front-end.
*(Note: `GameMode` lives in `config.py`, not here — keep that.)*

### `boneglaive/graphical/ui/panel_decorations.py` — 266 lines — **HIGH**
Entire file dead. All 7 public functions (`create_dust_texture`, `create_bone_texture_overlay`, `draw_industrial_border`, `draw_furniture_motif`, `draw_corner_decoration`, + helpers) and its 7 `COLOR_*` constants are unreferenced. Added alongside `motor_animation.py` (which *is* used); the decoration half was never wired in.

### `boneglaive/graphical/ui/animated_background.py` — ~160 lines — **HIGH**
`AnimatedBackground` is imported at `main_menu.py:10` but **never instantiated** (`AnimatedBackground(` = 0 hits tree-wide). The menu actually uses `KaleidoscopeBackground` (`main_menu.py:24`). The class + all its draw helpers are dead, and the `main_menu.py:10` import is a dead import.

### `boneglaive/game/animations.py` — 23 lines — **HIGH**
The whole file defines only `get_line(y0, x0, y1, x1)` (a Bresenham helper) and is **never imported**. The live `get_line` everyone uses is `utils/coordinates.get_line` (a `Position`-based variant). The `# import animations` comment in `renderer.py:16` refers to the *graphical* animations package, not this module.

### `boneglaive/utils/animation_helpers.py` — 29 lines — **HIGH**
The whole file defines only `sleep_with_animation_speed(duration)` and is **never imported**. Leftover from the curses-era animation pacing; graphical animations do their own timing.

---

## 2. `utils/event_system.py` — the pub/sub bus is a dead harness — **HIGH**

**There is not a single `.publish(...)` call in the entire codebase.** The only consumer is `engine.py:93`, which subscribes to `EFFECT_EXPIRED` — an event that is never published — so its handler `_handle_effect_expired` (`engine.py:6082`, empty body) can never fire. Everything publish-side is therefore unreachable:

- **25 `EventType` members never published or subscribed** (`event_system.py:13-63`): `GAME_INITIALIZED`, `TURN_STARTED/ENDED`, `GAME_OVER`, `UNIT_SELECTED/DESELECTED`, `CURSOR_MOVED`, `MODE_CHANGED`, `MOVE_/ATTACK_PLANNED/EXECUTED/CANCELLED`, `PLAYER_CHANGED`, `MESSAGE_LOGGED`, `HELP/LOG/CHAT/DEBUG_TOGGLED`, `UI_REDRAW_REQUESTED`, `MESSAGE_DISPLAY_REQUESTED`, `SELECT/MOVE/ATTACK/SKILL/TELEPORT_MODE_REQUESTED`, `CANCEL_REQUESTED`, `SETUP_PHASE_*`, `UNIT_PLACED`. Most are curses-UI-era. (`EFFECT_EXPIRED` is the 26th — subscribed, never published.)
- **`EventData` base + 14 typed data classes** (`:66, :149-239`) — never constructed.
- **`EventManager.publish` (:125), `.unsubscribe` (:114), `.clear_all_subscribers` (:142)** — zero call sites.
- Unused imports `Dict`, `List` (:7).

**Recommendation:** delete `EFFECT_EXPIRED` + the subscribe line (`engine.py:93`) + `_handle_effect_expired` (`engine.py:6082-6101`), then the whole `event_system.py` file can go. (If you'd rather keep a bus for future use, at minimum delete the 25 unused events, the 14 data classes, and `publish`/`unsubscribe`/`clear_all_subscribers` — but since nothing publishes, removing the file is cleaner.)

---

## 3. `graphical/sound_registry.py` — dead sound tables — **HIGH**

Sounds are played by `play_sound("string_key", ...)` directly in the animation modules, bypassing these tables entirely:

- **`MULTI_EVENT_SOUNDS`** (:141-446, **~305 lines**) — a large dict with **zero readers** anywhere.
- **`get_impact_sound` + `IMPACT_SOUNDS`** (:461 / :111) — 0 external refs.
- **`get_ui_sound` + `UI_SOUNDS`** (:474 / :120) — 0 external refs.
- **`get_music_track` + `MUSIC_TRACKS`** (:487 / :132) — 0 external refs.

Live and to keep: `SKILL_SOUNDS` + `get_sound_for_skill` (used by `animation_factory.py`).

---

## 4. `game/recruitment.py` — dead recruitment subsystem — **HIGH**

Only the module-level list `RECRUITMENT_ORDER` (:16) is imported anywhere (engine, setup UIs, tests). The entire class hierarchy is **never instantiated outside the file** — the graphical setup flow reimplements recruitment in `engine.py`:

- `RecruitmentPhase` enum (:19), `PlayerUnitPool` dataclass (:27) + 6 methods, `PlayerRecruitment` dataclass (:79) + methods, `RecruitmentSystem` class (:121) + 10 methods, and the module-global `recruitment_system` instance (:240).

Keep `RECRUITMENT_ORDER`; delete the rest.

---

## 5. Orphaned game mechanics (removed units/features, partially wired)

### 5a. Backhand — orphaned status effect from a removed melee unit — **HIGH**
**`backhand_active` is never set to `True` anywhere.** The mechanic is half-present across five files:
- `engine.py:4398-4417` — decrements `backhand_duration`, sets `backhand_active = False` (but nothing ever activates it).
- `graphical/ui/status_effects.py:293-299` — a status-bar icon definition for `"backhand_active"` that can never display.
- `graphical/game_state.py:957` & `renderer.py:3291` — "skill reflected by Backhand" checks, permanently false.
- `graphical/animations/animation_factory.py:1249-1283` — `BackhandAnimation` / `BackhandReflectionAnimation` branches (the classes don't exist — see 5b).

This is the same removed unit that left `MatadorAnimation`/`PoachAnimation` factory branches. Remove the whole cluster together.

### 5b. Phantom animation-factory branches — **HIGH**
`animation_factory.py` has `elif anim_class.__name__ == "X"` branches for classes that **do not exist anywhere**: `MatadorAnimation` (:1221), `PoachAnimation` (:1234), `BackhandAnimation` (:1249), `BackhandReflectionAnimation` (:1266). They can never match. Plus two **exact-duplicate** branches that are unreachable (first match wins): `DerelictBuildingFormation` (:1284, dup of :979) and `DerelictBuildingTiles` (:1295, dup of :992). And a dead import `SiteInspectionBuff` (:20).

### 5c. `is_protected_from` — dead Saft-E-Gas protection — **HIGH**
`engine.py:1560` `is_protected_from(...)` unconditionally `return False` (the Saft-E-Gas targeting-protection sub-feature was removed). It is still *called* at `engine.py:1649, 3280, 3314, 3695`, making all four **permanently-false dead branches**. (Saft-E-Gas itself still exists elsewhere as a vapor variant — only this protection check is dead.)

### 5d. Tile-lighting subsystem — write-only — **HIGH/MED**
The lamp-lighting data is built but never consumed (the renderer derives lamp glow independently):
- Dead readers (0 callers): `map.py` `get_lighting_at` (:240), `is_illuminated` (:244), `get_illumination_color` (:253). **HIGH**
- Orphaned producers: `lighting_effects` (init :78), `set_lighting_effect` (:224), `setup_tiffany_lamp_lighting` build data nothing reads. **MED**

### 5e. `gaussian_charging` — dead guard — **MED**
`units.py:562` `if hasattr(self,'gaussian_charging') and self.gaussian_charging:` — `gaussian_charging` is **never assigned** anywhere (also read dead in `loto_system.py:83`). The live FOWL_CONTRIVANCE charging flag is `charging_status` (`engine.py:2601`). Always-false branch.

### 5f. `AETHERIC_CURLER` — "coming soon" placeholder for an unbuilt unit — **HIGH (unreachable)**
A teaser scaffold keyed by the string `"AETHERIC_CURLER"`, but there is no such `UnitType` (the roster is built from `RECRUITMENT_ORDER`, enums only). Every guard comparing the selected unit to this string is unreachable:
- `setup_unit_help.py` — dict block :378-400, `should_flash` (:618), `needs_animation` (:925), `isinstance(unit_type, str)` branches (:74, :495, :649-656, :661).
- `setup_window.py` — `is_placeholder` branches at :427-499 ("COMING SOON" tile) and :564-585 ("Stats unknown").

*(Related: `.gitignore:94` references a `AETHERIC_BILLMAN.md` scratch doc — same unbuilt-unit lineage.)*

### 5g. Network-multiplayer scaffolding — `top_bar.py` — **HIGH**
`TopBar` is built with no network args, so `is_network_game` is permanently `False`. Dead: `set_network_state` (:77), `trigger_turn_pulse` (:82), `trigger_gp_pulse` (:86) — 0 callers; `_draw_network_status` (:307, behind the dead flag); `mode_transition_time` (:54, write-only); and three abandoned left-section methods `_draw_player_info` (:132), `_draw_turn_info` (:152), `_draw_mode_indicator` (:288).

---

## 6. Dead methods & classes (in otherwise-live files) — **HIGH** unless noted

### `game/engine.py`
`change_map` (:130) · `remove_last_setup_unit` (:738) · `resolve_unit_conflicts` (:939) · `is_adjacent` (:1108) · `get_attack_range_tiles` (:1753) · `get_ossify_defense_bonus` (:1809) · `_release_trapped_units` (:5089) · `toggle_test_mode` (:5840) · `get_game_state` (:6104, a different live `get_game_state` exists on the graphical adapter).
- `_handle_effect_expired` (:6082) — empty body, never fires (see §2). **MED**
- `DeadUnit.dominion_permanent_attack` (:29) — kept "for save compatibility" per its comment; legacy Dominion system. **LOW** (back-compat read in respawn — confirm before removing).

### `game/units.py`
`_teleport_derelictionist_away` (:1763, the **Game** method of the same name is the live one) · `_trigger_abreaction` (:1795, handled inline in Vagal Run) · `get_skill_by_key` (:1754).
- `process_interferer_effects` (:1746) — comments-only body; *called* at `engine.py:2868` but does nothing. **MED**

### `game/map.py`
`LimeFoyerMap` class (:543) — never instantiated; `MapFactory` builds `NewLimeFoyerMap` for "lime_foyer". · `is_rail_junction` (:403) · `to_json` (:507, no map-save path exists). Plus lighting readers (§5d).

### `ai/strategic_planner.py` & `ai/battlefield_analyzer.py`
`should_be_aggressive` (:223) · `should_prioritize_safety` (:235) · `get_objective_priority` (:247) — 0 callers. · `battlefield_analyzer.is_position_safe` (:307) — 0 callers; its helper `get_threat_at_position` (:293) is then transitively dead. **MED**

### `ai/tactical_evaluator.py`
`is_skill_upgraded` dead branches at :182 and :918 — the AI never equips upgrades, so the upgraded branch is unreachable; only the `else` runs. **MED**

### `graphical/renderer.py`
`draw_grid_old` (:3972, self-labeled "OLD IMPLEMENTATION - kept for reference") · `setup_demo_scene` (:354) · `_handle_cursor_movement` (:5632, never wired into the event loop) · `COLOR_BG` (:88, unused) · `main()` (:5675, dead `__main__` entry — the real entry is `run_graphical.py`). **MED for `main()`**

### `graphical/game_state.py` — stub adapter methods (all `return []`/`False`/`None`, 0 callers)
`get_pending_animations` (:1353) · `get_game_state` (:1547) · `get_valid_targets` (:1566) · `is_game_over` (:1580) · `get_winner` (:1584). · `handle_player_action` (:1495) is live but only the `"target_skill"` branch is ever reached — `select_unit`/`select_skill`/`move_unit`/`end_turn` are dead branches. **MED**

### `graphical/ui_adapter.py` — dead/test-only animation stubs
`show_skill_animation` (:78, test-only `hasattr` probe; also has a latent unbound-var bug) · `show_movement_animation` (:119, test-only) · `show_death_animation` (:141, 0 callers; calls a nonexistent `"unit_death"` sound) · `_render_and_wait` (:184, blocking `time.sleep` text-mode pattern, 0 callers).
*Keep:* `show_attack_animation` (live, engine), `draw_board` (live no-op hook), spinner methods.

### `graphical/camera.py`
`screen_to_grid` (:61, the renderer has its own) · `set_zoom` (:90) · `get_tile_size` (:86) · `update_layout` (:97) — all 0 callers.

### `graphical/sound_manager.py`
`stop` (:144) · `preload_sounds` (:177) · `clear_cache` (:188) · `init_sound_manager` (:211) — 0 callers. · unused `import os` (:7).

### `graphical/ui/` widgets — misc dead methods
- `setup_unit_help.py` — **shadowed duplicate `handle_click`** (:413, overridden by :436 — the first is unreachable).
- `setup_window.py` — `select_next` (:132), `select_prev` (:138), `_draw_selected_stats` (:557).
- `unit_info.py` — `_draw_stat_line` (:594, superseded by inline `_draw_stats`).
- `skill_bar.py` — `get_tooltip` (:400).
- `status_effects.py` — `handle_click` (:573). `handle_mouse_motion` (:568) is a live no-op stub. **MED**
- `font_utils.py` — `clear_font_cache` (:158), `FontCache.clear` (:40), `get_fitted_font` (:49, internal-only). **MED on get_fitted_font**
- `scale_utils.py` — `ScaleManager.scale_tuple` (:95).

### `utils/coordinates.py` & `utils/debug.py`
- `get_positions_in_range` (:65) · `Position.as_tuple` (:44) · `Position.is_in_bounds` (:61) — 0 callers. (Keep `Position.distance_to` — reached via `is_adjacent`.)
- `debug.get_debug_overlay` (:129, curses overlay) · `game_assert` (:118) · `DebugConfig.toggle`/`toggle_overlay`/`toggle_perf_tracking` (:64/:69/:74, curses-era keybind handlers). **MED on the toggles**

### `utils/constants.py`
`DESCRIPTORS_BY_TYPE` (:83) — built from `UNIT_DESCRIPTORS`, never read.

---

## 7. Unused module-level constants

- **`COLOR_SKILL`** imported-unused in 5 animation files: `delphic_appraiser.py`, `derelictionist.py`, `fowl_contrivance.py`, `marrow_condenser.py`, `potpourrist.py` (all line 9).
- **Animation color constants** (defined once, never read): `core.py` `COLOR_MELEE_SLASH` (:29), `COLOR_IMPACT` (:30); `interferer.py` `COLOR_FLASH_BRIGHT` (:15); `landscaper.py` `BONE_WARM` (:28), `METAL_LIGHT` (:37); `ordnance_graft.py` `OLIVE_LIGHT` (:27); `motor_animation.py` `COLOR_BONE_WHITE` (:18).
- **UI theme constants** (defined-only): `game_over_window.py` `MINIMIZED_*` (:36-39), `COLOR_VICTORY`/`COLOR_DEFEAT` (:18-19), `COLOR_OVERLAY` (:10); `concede_dialog.py` `COLOR_OVERLAY`/`COLOR_TEXT_DIM` (:10/:17); `respawn_window.py` & `setup_exit_dialog.py` `COLOR_OVERLAY`; `menu_components.py` `COLOR_BG_DARK` (:11); `help_page.py` `LINE_SPACING` (:29, write-only).
- **Write-only skill attributes:** `landscaper.py` `fire_source` (set at :276/:645, nulled :346/:596/:970, never read) · `marrow_condenser.py` `OssifySkill.upgraded` (:92), `BoneTitheSkill.upgraded` (:646) · `fowl_contrivance.py` `FragcrestSkill.upgraded_target_type/range/area` (:772-774) · `mandible_foreman.py` `effect_symbol` (:521/524/533/536/544, ASCII-era display leftover).

---

## 8. Unused imports & locals (mechanical — `pyflakes`)

`pyflakes` reports **~165 unused imports** and **~85 unused local variables** across the package. These are safe, high-volume cleanups. Highlights:

- **Dead `import time`** (curses-pacing residue, `time` never called): `grayman.py` (:124/377/553), `marrow_condenser.py` (:132/309/695), `gas_machinist.py` (:177/325/495/865).
- **Dead `import random`**: `marrow_condenser.py:8`, `interferer.py:8`, `derelictionist.py:11`, `gas_machinist.py:7` (module-level, shadowed by a local re-import in one method), `fowl_contrivance.py:9` (ditto).
- **Dead `import os`**: `config.py:8`, `sound_manager.py:7`, `skill_bar.py:7`, `status_effects.py:7`, `loto_system.py:8`, `unit_status_bar.py:7`, and **7× inner `import os`** in `action_menu.py` (`ActionButton.draw`).
- **Dead typing imports**: `Dict/List` (event_system :7), `Dict` (constants :4), `Optional` (upgrades :7, skill_simulator :7), `Tuple` (strategic_planner :8), `Set` (battlefield_analyzer :7), assorted in gas/fowl/landscaper/delphic skills.
- **Dead engine imports**: `logging` (:3), `GameMap` (:9), `Position` (:10, every real use re-imports locally), `CRITICAL_HEALTH_PERCENT` (:1835), `ORDNANCE_DRONE_REGEN` (:5329), repeated `message_log`/`MessageType` local re-imports, `math` (:5483).
- **`Skill`** imported-unused in `units.py:10` and `skills/__init__.py:8`.

> Run `python -m pyflakes boneglaive run_graphical.py setup.py` for the full machine-checkable list. Note pyflakes also reports **24 "f-string is missing placeholders"** (style, not dead) and **63 "redefinition of unused"** (mostly the intentional local re-import pattern — benign).

---

## 9. Top-level / packaging dead spots

- **`setup.py:36`** — `entry_points` → `'boneglaive=boneglaive.main:main'`, but **`boneglaive/main.py` was deleted** in the ASCII removal. Broken console-script entry. The `description` ("terminal tactical combat") and `keywords` ("terminal curses nix unix") are also stale (the shipped game is graphical-only).
- **`run_graphical.py:76`** — `selected_map` defaults to `'edgecase'`, but **no `edgecase.json` exists** (maps are `hard_pressed`, `lime_foyer`, `stained_stones`, `verdant_terrace`). Harmless today because `config.json` overrides it with `hard_pressed`, but it's a wrong default that would load an empty map if config is missing. Suggest `'hard_pressed'`.

---

## 10. Latent bugs found along the way (NOT dead code — flagged for awareness)

These are not cleanup targets but surfaced during the sweep:

- **Import shadowed by a loop variable** (the import becomes unusable later in scope): `message_log.py:374` (`re`), `interferer.py:1762/1780/1803/1938` (`Particle`, `TILE_SIZE`).
- **`ui_adapter.show_skill_animation`** references `target_grid_y`/`target_grid_x` before assignment when `target_pos` is falsy — dead method, but a real unbound-variable bug if it were ever called.
- **`graphical/animations/__init__.py:194`** — `__all__` lists `'BoneTitheAnimationUpgraded'`, which **doesn't exist** → `from ...animations import *` would raise. (The `__all__` list is generally unmaintained: `BoneChunkProjectile` and `BoneTitheDeathHealAnimation` are imported but missing from it.)
- **Not a bug, noted to prevent a wild-goose chase:** `pyflakes` flags `glaiveman.py:947` `prev_x`/`prev_y` as undefined — this is a **false positive**; the `if j > 0:` guard ensures the prior-iteration assignment at :948 always ran first.

---

## Verified LIVE (do **not** remove — common false-positive traps)

- **No orphaned *skill* classes** — every skill in `game/skills/` is registered in `registry.py` or dynamically instantiated on upgrade/summon (`AerosolizeArmsSkill`, `ParallaxSkill`, `DeftRerollSkill`, `DroneInoculantSkill`).
- **All 12 basic-attack animation classes** — instantiated in `renderer.py._create_attack_animation` by `unit.type`.
- **All per-unit AI evaluators** (`_evaluate_<unit>_skills`) — dispatched via `unit.type` early-return chains in `tactical_evaluator.py`. The ORDNANCE evaluators + approach-gradient block are live.
- **`vulture`'s 60%-confidence bucket (430 items)** is mostly false positives — public methods it can't see being called via dynamic dispatch. The findings above used 80%+ vulture plus manual per-symbol grep verification.
- **No ASCII/curses dead branches remain** — zero `display_mode`/`is_text_mode`/`import curses`/`boneglaive.ui`/`boneglaive.renderers` references. That cleanup is complete; this audit is the layer beneath it.
- `event_system.EventManager`/`subscribe`/`get_event_manager`, `draw_board` no-op hook, `menu_manager.cleanup` no-op, `MessageType.PLAYER/ERROR/DEBUG` (consumed internally), `Position.distance_to`, `interferer.NeutronIlluminant.trigger_flash_effect` (a no-op but **called live** — dead *effect*, not dead symbol).

---

## Suggested removal order (low-risk → higher-touch)

1. **Unused imports/locals** (§8) — mechanical, `pyflakes`-checkable, zero behavior change.
2. **Whole-file orphans** (§1) — delete `skill_simulator.py`, `pathfinding.py`, `multiplayer_manager.py`, `panel_decorations.py`, `animated_background.py`, `game/animations.py`, `animation_helpers.py` (+ their import/construction lines).
3. **Dead data tables** (§3 sound tables, §2 event bus, `DESCRIPTORS_BY_TYPE`).
4. **Dead methods/classes** (§6) and **unused constants** (§7).
5. **Orphaned mechanics** (§5) — Backhand cluster, `is_protected_from` + its 4 callers, lighting subsystem, `gaussian_charging` guard, `AETHERIC_CURLER` placeholder, network scaffolding. (Touch more files each; do as focused commits.)
6. **Packaging fixes** (§9).

**Regression net:** after each batch, run
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_headless_combat.py` (all units' attacks+skills),
`tests/test_ordnance_graft.py`, `tests/test_ordnance_graft_ai.py`,
and a headless boot `timeout 12 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python run_graphical.py` (exit 124 = booted OK).
