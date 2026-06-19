# Decoupling Boneglaive from its ASCII Base — Plan (A + C)

**Goal:** Make `run_graphical.py` (SVG mode) the sole front-end, eliminate the
"design a unit in ASCII first" step, and collapse scattered per-unit graphical
registration into a single data-driven descriptor table.

**Scope chosen:** A (remove ASCII/hybrid front-ends) + C (data-drive graphical
unit registration). Deliverable **B** (stripping the now-dead inline-ASCII
animation calls out of `game/`) is **deferred** — it has no visible effect
because the SVG renderer already no-ops those calls.

---

## Key facts established by investigation (why this is safe)

1. **The SVG graphical mode is already independent of ASCII code.**
   - `run_graphical.py` / `boneglaive/graphical/**` import **nothing** from
     `boneglaive.ui`, `boneglaive.renderers`, `boneglaive.main`, `curses`, or
     `RenderInterface`. (verified by grep — all empty)
   - Graphical mode calls `game.execute_turn(ui=None)` (`graphical/renderer.py:4669`)
     and reconstructs animations from state-diffs via `GameStateAdapter` +
     `AnimationFactory`.
   - The engine's inline-ASCII animation calls resolve to **no-op stubs** in
     graphical mode: `graphical/renderer.py:502-512`
     (`animate_attack_sequence`, `draw_damage_text`, `refresh` all `pass`).

2. **The shipped binary already excludes curses.**
   - `boneglaive.spec:76` Analysis target is `['run_graphical.py']`.
   - `boneglaive.spec:105` `excludes=['curses', '_curses']`.
   - => ASCII mode is dev-only; release is already graphical-only. Phase A just
     formalizes this.

3. **`game/` has no static import of `ui/` or `renderers/`.** The only coupling
   is runtime duck-typed `self.ui.renderer.*` calls, all guarded by
   `if ui and hasattr(ui,'renderer')`. Deferred to B.

4. **AI references to curses `GameUI` are TYPE_CHECKING-only** (type hints):
   `ai/ai_interface.py:13`, `ai/smart_ai.py:18`. Runtime is duck-typed. Trivial
   to neutralize.

---

## Three renderer paths today (only #3 survives)

| # | Entry | Stack | Fate |
|---|-------|-------|------|
| 1 | `main.py` (text) | `ui.GameUI` + `renderers.CursesRenderer` | DELETE |
| 2 | `main.py` (graphical display_mode) | `ui.GameUI` + `renderers.PygameRenderer` (ASCII grid in pygame) | DELETE |
| 3 | `run_graphical.py` | `graphical.GraphicalRenderer` + `GameStateAdapter` (SVG) | **KEEP — sole entry** |

---

# PHASE A — Remove ASCII / hybrid front-ends

**Deletion footprint:** `boneglaive/ui/` + `boneglaive/renderers/` = 11 files,
~11,410 LOC, plus `boneglaive/main.py`.

### A1. Delete entry point & front-end packages
- [ ] `boneglaive/main.py`
- [ ] `boneglaive/ui/` (entire dir — curses `GameUI`, `MenuUI`, `ui_components.py`,
      `ui_renderer.py`, `pygame_game_ui.py`, `components/recruitment_menu.py`, …)
- [ ] `boneglaive/renderers/` (entire dir — `curses_renderer.py`,
      `pygame_renderer.py`, `__init__.py`)
- [ ] `boneglaive/utils/render_interface.py` (`RenderInterface` ABC + `RenderBackend`)

### A2. Neutralize TYPE_CHECKING hints that referenced curses GameUI
- [ ] `boneglaive/ai/ai_interface.py:13` — drop `from boneglaive.ui.game_ui import GameUI`;
      change `ui: Optional['GameUI']` → `ui: Optional[object]` (or a small Protocol).
- [ ] `boneglaive/ai/smart_ai.py:18,24,30` — same treatment.

### A3. Remove DisplayMode / text-mode config
- [ ] `boneglaive/utils/config.py` — remove `DisplayMode` enum + any
      `display_mode` default/validation. Keep `GameMode`.
- [ ] `config.json` — remove `display_mode` key.
- [ ] Confirm no remaining `display_mode` readers after A1 (was only `main.py`,
      `ui/*`, `pygame_renderer.py` — all deleted).

### A4. Prune text-mode branches in shared `utils/asset_manager.py`
- [ ] Remove the **text-mode** `animation_sequences` (ASCII frame lists,
      `~:120-251`) and text `effect_tiles` (`~:106-117`). KEEP whatever the SVG
      pipeline reads. (Graphical uses `AnimationFactory`, not these — verify each
      dict has no graphical consumer before deleting.)
- [ ] Re-check: `get_unit_tile()` / `get_skill_animation_sequence()` — keep only
      if `graphical/` still calls them; otherwise remove.

### A5. Trim ASCII-only symbol tables in `utils/constants.py`
> ⚠️ Verify each is unused by `graphical/` before removing — some are read by
> `graphical/ui/unit_status_bar.py`.
- [ ] `UNIT_SYMBOLS` (`:49-64`) — ASCII map glyphs. After B these lose their last
      `game/` reader (`engine.py:1396`); for now keep if `graphical` reads them.
- [ ] `ATTACK_EFFECTS` (`:83-98`) — ASCII attack chars. Likely deletable.
- [ ] `STATUS_EFFECT_SYMBOLS` (`:147-156`) — ASCII status glyphs. Keep iff graphical
      status panel reads it; else delete (graphical uses `status_effects.py` entries).
- [ ] KEEP: `UnitType`, `UNIT_STATS`, `GP_ELIGIBLE_UNITS`, `UNIT_ID_ALPHABET`
      (identity logic), `UNIT_DISPLAY_NAMES`.

### A6. Smoke test
- [ ] `python run_graphical.py` boots to menu, start a VS_AI game, play a full
      turn with attacks + a skill from each unit type, trigger a respawn, open
      unit help, open upgrade window. No exceptions; animations intact.
- [ ] `grep -rn "boneglaive.ui\|boneglaive.renderers\|render_interface" boneglaive/`
      → only stale `.pyc` (clean `__pycache__`).

**Phase A payoff:** ASCII authoring step gone. Per-unit touchpoints drop by the
entire **(B) column** (~8 sites): ASCII skill-menu block, ASCII attack-anim
special-case, ASCII help-toggle, `base_units` list, ASCII help/lore page,
`UNIT_SYMBOLS`/`ATTACK_EFFECTS` entries, text asset_manager sequences.

---

# PHASE C — Data-drive graphical unit registration

**Target:** Replace scattered `elif unit.type == X` dispatch (**33 sites** in
`graphical/`) and **2 hardcoded unit lists** with one descriptor table, so adding
a unit = (1) skill file, (2) one descriptor entry, (3) asset files.

### C0. Inventory the per-unit graphical touchpoints to fold in
(from the unit-add map; all under `boneglaive/graphical/` unless noted)
- Sprite: `graphics/units/{name}.svg` (convention-loaded — stays an asset)
- Skill icons: `graphics/skill_icons/{skill}.svg` (asset)
- Animations file: `graphical/animations/{unit}.py` (stays per-unit code)
- `animations/animation_factory.py` — `SKILL_ANIMATIONS` import + map (`~:84-90, 204-209`)
- `renderer.py:3187-3202` — per-unit basic-attack dispatch + type list
- `sound_registry.py:97-101, 390-412` — `SKILL_SOUNDS` map + sound-file defs
- `game_state.py:1269-1291` — persistent-effect event detection (slag/topiary)
- `ui/setup_window.py:70-97` — `unit_types` list + `unit_names` map  ← unify
- `ui/setup_unit_help.py:49, 341-363, 474-495` — `unit_names` + help block + sprite loader  ← unify
- `ui/status_effects.py:118-125` — status entry (only if unit adds a status)
- Shared: `utils/unit_help_data.py` (canonical help data — make descriptor point here)

### C1. Design the descriptor (new module, e.g. `boneglaive/game/unit_registry.py`
or `boneglaive/utils/unit_descriptors.py`)
A single ordered mapping `UnitType -> UnitDescriptor` with fields:
```
UnitDescriptor(
    unit_type, display_name, symbol(optional/legacy),
    selectable=True, recruit_order_index,
    sprite="units/landscaper",            # convention key
    skills=[passive, a1, a2, a3],         # names -> drives icons/anim/sound lookups
    skill_icons={skill: "skill_icons/..."},
    attack_animation=<class or key>,      # replaces renderer.py:3187 elif
    skill_animations={skill: AnimClass},  # replaces animation_factory map
    skill_sounds={skill: "wav key"},      # replaces sound_registry map
    persistent_effects=[...],             # drives game_state event detection
    status_effects=[...],                 # drives status_effects.py entries
    help_ref=<key into unit_help_data>,
)
```
Single source of truth for **selection order, names, sprite, skills, icons,
animations, sounds, help**.

### C2. Replace the 2 hardcoded lists
- [ ] `ui/setup_window.py` `unit_types`/`unit_names` → derive from descriptors
      (`[d.unit_type for d in DESCRIPTORS if d.selectable]`, `{d.unit_type: d.display_name}`).
- [ ] `ui/setup_unit_help.py` `unit_names` + per-unit help block → derive from
      descriptors + `unit_help_data`.

### C3. Replace the 33 type-dispatch sites (highest value, do incrementally)
- [ ] `renderer.py:3187-3202` basic-attack dispatch → `descriptor.attack_animation`.
- [ ] `animation_factory.py` `SKILL_ANIMATIONS` → built by iterating
      `descriptor.skill_animations`.
- [ ] `sound_registry.py` `SKILL_SOUNDS` → built from `descriptor.skill_sounds`.
- [ ] `game_state.py:1269-1291` persistent-effect detection → loop over
      `descriptor.persistent_effects`.
- [ ] `status_effects.py` entries → built from `descriptor.status_effects`.
- [ ] Sweep remaining `unit.type ==` / `attacker.type ==` in `graphical/` and
      route each through the descriptor or a registry lookup.

### C4. (Optional, ties into A5) Make `recruitment.py` `RECRUITMENT_ORDER` derive
from descriptor order so there is **one** ordering, not two.

### C5. Verify "add a unit" is now minimal
- [ ] Dry-run: document the new add-a-unit checklist. Target: skill file +
      animations file + 1 descriptor entry + asset SVGs/WAVs. (~3 code edits vs ~20.)
- [ ] Regression smoke test = A6 again (all units selectable, animate, sound,
      help, status icons correct).

---

## Suggested execution order
1. Branch off `main` (`decouple-ascii`).
2. **Phase A** in one pass (A1→A5), then A6 smoke test + commit.
   (Low risk; SVG game untouched functionally.)
3. **Phase C** incrementally: C1 (descriptor) → C2 (lists) → C3 site-by-site,
   smoke-testing after each cluster. Commit per cluster.
4. (Later/optional) **Phase B** — strip dead inline-ASCII anim from `game/`.

## Risks / watch-items
- **A4/A5 over-deletion:** some `constants.py` symbol tables and `asset_manager`
  entries ARE read by `graphical/ui/unit_status_bar.py`. Grep each symbol's
  consumers before removing; when in doubt, keep.
- **C3 behavior parity:** the `elif` blocks may hide per-unit quirks (special
  attack frames, conditional effects). Port each faithfully; smoke-test per unit.
- **`unit_help_data.py` may be partial** (LANDSCAPER not found in it) — confirm
  which help path graphical actually uses before pointing descriptors at it.
- Keep `UNIT_ID_ALPHABET` and `UNIT_STATS`/`GP_ELIGIBLE_UNITS` — these are core
  logic, not ASCII.
