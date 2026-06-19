# Making New Units Easier to Add — Plan

**Goal:** Shrink "add a playable unit" from ~16 manual edits across a dozen
files (several of which fail *silently* when forgotten) down to **one descriptor
entry plus the genuinely creative work** (skill logic + animations + art).

**Context:** The v1.4 ASCII-decoupling refactor (`DECOUPLE_ASCII_PLAN.md`,
Phases A/B/C, all committed) removed the curses front-end and the "design in
ASCII first" step. This plan is the natural follow-on: now that there's a single
front-end, the *data* describing a unit is still scattered and duplicated. This
finishes the job on the registration side.

**Status:** Proposal. Nothing implemented. All work would be local commits on
`v1.4` (no pushing — see workflow prefs).

---

## The problem, concretely

Adding a unit today touches these MANDATORY sites (traced from LANDSCAPER):

| File | What you must add |
|------|-------------------|
| `utils/constants.py` | enum member, `UNIT_STATS` tuple, `UNIT_SYMBOLS`, `UNIT_DISPLAY_NAMES`, `GP_ELIGIBLE_UNITS` (5 spots) |
| `game/recruitment.py` | `RECRUITMENT_ORDER` entry |
| `game/skills/registry.py` | skill-class import + `UNIT_SKILLS["NAME"]` mapping |
| `graphical/animations/animation_factory.py` | anim-class import + `SKILL_ANIMATIONS` entries |
| `graphical/sound_registry.py` | skill→sound map + sound-file paths |
| `utils/asset_manager.py` | **2** ASCII attack-effect maps + an `animation_sequences` entry |
| `utils/unit_help_data.py` | full help entry |
| `graphical/ui/setup_unit_help.py` | a SECOND, separate `simplified_info` entry |
| `graphics/units/<name>.svg` + `graphics/skill_icons/<skill>.svg` | art assets |

Plus three AI roster pools in `engine.py` (~L213, ~L503, ~L639) that are
hand-copied duplicates of `RECRUITMENT_ORDER` — forget one and the AI silently
won't field the unit.

### Why it bites (in plain terms)
- **Silent failures.** A typo'd registry key or a forgotten AI pool doesn't
  error — the unit just comes out with no skills, or the AI never uses it. You
  find out during playtesting, not at startup.
- **Duplicated data drifts.** The roster lives in 4 places; help text lives in
  2 places; stats are restated as text in the help page. This *already bit us*:
  LANDSCAPER was missing from the setup-help screen because one copy got
  forgotten (fixed in Phase C, commit `2cccc0f`).
- **Order-dependent tuples.** `UNIT_STATS` is a bare `(20, 1, 1, 2, 1)` — no
  field names, so a mis-ordered stat ships silently.
- **Dead leftovers to copy by mistake.** `ARCHER`/`MAGE` are ghost units still
  half-wired in `constants.py` and `asset_manager.py`; surviving ASCII attack
  maps in `asset_manager.py` are leftovers the decouple refactor didn't reach.

---

## Plan — three tiers, safest first

Each Tier-1 item is an independent, behavior-preserving commit, validated by the
existing headless harness `tests/test_headless_combat.py` (exercises all 11
units' basic attack + 32/33 skills) plus a `run_graphical.py` smoke test. Tier 2
is the payoff the earlier items set up. Tier 3 is optional polish.

### TIER 1 — Cleanups & safety nets (low risk, high clarity) — ✅ DONE

Committed on `v1.4`: `7969a05` (T1+T3), `2d82c88` (T2), `4155024` (T4).
Note: T4 uncovered a real drift bug — one of the four AI roster lists
(`setup_initial_units` player-2 branch) was missing LANDSCAPER, so that path
could never field one. Fixed by the unification.


**T1. Name the stat fields.**
- Replace the 5-tuple in `UNIT_STATS` with a `NamedTuple` / `@dataclass`
  `UnitStats(hp, attack, defense, move_range, attack_range)`.
- Update readers to use `.defense` etc. instead of positional indexing.
- *Benefit:* impossible to mis-order a stat; self-documenting.
- *Files:* `utils/constants.py` + every `UNIT_STATS[...]` reader (grep first).

**T2. Key the skill registry by `UnitType`, not strings.**
- `UNIT_SKILLS` is currently keyed by the enum *name string*
  (`"LANDSCAPER"`), looked up via `get_type_name()` in `units.py:206`.
- Re-key by `UnitType` members. A bad/missing key becomes a loud `KeyError`
  at lookup instead of a unit that silently has no skills.
- *Files:* `game/skills/registry.py`, `game/units.py`.

**T3. Delete dead leftovers.**
- Remove `UnitType.ARCHER` / `UnitType.MAGE` and their entries in
  `UNIT_STATS` (L34-35), `UNIT_SYMBOLS` (L51-52), `UNIT_DISPLAY_NAMES`
  (L113-114), and the `archer_attack`/`mage_attack` maps in
  `asset_manager.py` (L270-271, 290-291).
- Remove the surviving ASCII attack-effect machinery in `asset_manager.py`
  (`get_attack_effect`, `get_attack_animation_sequence`, the text
  `animation_sequences` used only by them) **after** confirming no
  `graphical/` consumer reads them (grep each; the decouple plan flagged
  `unit_status_bar.py` as the one to check — keep anything it uses).
- *Benefit:* cleaner template to copy; finishes the decouple cleanup.

**T4. One roster, not four.**
- Make the three AI unit pools in `engine.py` (~L213, ~L503, ~L639) derive
  from `RECRUITMENT_ORDER` instead of hand-copied lists.
- *Benefit:* adding a unit to the roster automatically lets the AI field it;
  no silent "AI never uses my unit" gap.
- *Watch:* preserve the existing "max 1 DERELICTIONIST" composition rule.

### TIER 2 — The single character sheet (the real payoff) — ✅ T5 DONE

Committed on `v1.4`: `47a6f72` (descriptor + derived identity/roster tables +
registry guard), `3110820` (help-page stats derived from UNIT_STATS).
Outcome vs. plan:
- Descriptor lives in `constants.py` (NOT a new `game/` module) because
  `constants.py` is a leaf module everything imports and must not reach down
  into skills. Skill wiring stays in `registry.py`, keyed by the same UnitType
  and guarded so a descriptor without skills fails loudly at import.
- `UNIT_STATS` / `UNIT_SYMBOLS` / `UNIT_DISPLAY_NAMES` / `GP_ELIGIBLE_UNITS` /
  `RECRUITMENT_ORDER` are all derived views (verified byte-identical to before).
- Help-page stat lines now generated from `UNIT_STATS`. This corrected two
  already-drifted units (GAS_MACHINIST, HEINOUS_VAPOR) — user approved.
- NOT done: unifying the two help PROSE tables (`unit_help_data` long-form vs
  `setup_unit_help` simplified_info). On inspection these hold genuinely
  different content for different UIs — not duplication — so merging them is not
  a clean win and was deliberately left.

**T5. Introduce a `UnitDescriptor` table.**
- New module (e.g. `game/unit_registry.py`): one ordered mapping
  `UnitType -> UnitDescriptor` owning the per-unit data:
  `stats, display_name, symbol, recruit_order, skills (passive+3 active),
  skill_icon/anim/sound keys, help_ref`.
- Make the existing tables *derived views* of it, one at a time, so each step
  is independently testable:
  - `UNIT_STATS` → built from descriptors (lands on T1's named stats).
  - `RECRUITMENT_ORDER` → descriptor order (lands on T4's single roster).
  - `UNIT_SKILLS` → built from `descriptor.skills` (lands on T2).
  - `UNIT_DISPLAY_NAMES` / `UNIT_SYMBOLS` / `GP_ELIGIBLE_UNITS` → derived.
  - Help: point `unit_help_data.py` and `setup_unit_help.py simplified_info`
    at a single `help_ref`, and **generate** the restated stat lines
    (`'HP: 22'`) from `descriptor.stats` so they can't drift.
- *Benefit:* a unit's identity lives in ONE entry. Adding a unit = fill out
  one descriptor; every table updates itself; nothing can fall out of sync.
- *Note:* Phase C of the decouple refactor scoped the descriptor *down* after
  finding `SKILL_ANIMATIONS`/`SKILL_SOUNDS` already centralized. That's still
  true — so this descriptor focuses on the data that's STILL duplicated
  (roster, names, stats, help, skill wiring), not the anim/sound tables.

**T6. Flatten the animation-factory dispatch.** *(optional — NOT RECOMMENDED after review)*
- `animation_factory.py` has a ~55-rung `elif anim_class.__name__ == "..."`
  ladder inside the `SKILL_ANIMATIONS` lookup.
- **Finding (2026-06-19):** each rung constructs its animation with a genuinely
  different, hand-tuned signature (different kwargs, fallbacks, early-returns on
  missing target_pos, some pass `game`). This is per-animation glue, not
  mechanical boilerplate. Flattening it means inventing a uniform construction
  protocol implemented by all ~55 animation classes — large, invasive, touches
  every animation file, high regression risk, ZERO player-visible benefit.
  Payoff (one fewer edit when adding a skill anim) ≪ risk. **Recommend skipping.**
- **Separate, safe sliver — ✅ DONE (`58ad351`):** removed the dead debug
  scaffolding (39 husks: whole dead `if "GAUSSIAN"/"DEMILUNE"` blocks +
  `pass`-before-`return None`). Kept the one real no-op (sound-except body).
  Behavior unchanged; ladder + SKILL_ANIMATIONS intact. CODE_STANDARD §1 fixed.

### TIER 3 — Scaffolding (nice-to-have)

**T7. `scaffold_unit.py` generator.**
- A small script: given a name + stats, stamp out the skill-file stub, the
  `graphical/animations/<unit>.py` stub, the descriptor entry, and
  placeholder asset filenames.
- *Benefit:* turns "remember all the spots" into "run one command, then write
  the skills + animations + art" — the only parts that are actually creative.

---

## Suggested order
1. **T1, T2, T3, T4** — independent safe commits, harness + smoke test each.
2. **T5** — build the descriptor, then convert tables to derived views one at a
   time (each conversion its own commit + test). This is where the "one
   character sheet" win lands.
3. **T6** — only if the animation ladder is worth flattening; highest-risk item.
4. **T7** — once the descriptor is the single source, the generator is easy.

## Risks / watch-items
- **T3 over-deletion:** some `asset_manager`/`constants` symbol tables are read
  by `graphical/ui/unit_status_bar.py`. Grep each symbol's consumers before
  removing; when in doubt, keep. (Same caution the decouple plan raised.)
- **T4:** keep the AI's "max 1 DERELICTIONIST" rule and the duplicate-prevention
  logic — only the *source list* changes, not the selection rules.
- **T5 help generation:** confirm which help path the graphical UI actually uses
  before pointing both tables at one `help_ref` (Phase C notes `unit_help_data`
  was partial historically).
- **T6 parity:** the `elif` rungs may encode per-animation quirks; port and
  smoke-test each individually.

## Definition of done
- Adding a unit = 1 descriptor entry + skill file + animations file + assets.
- No duplicated roster/help/stat data; forgetting a wiring step fails loudly
  (import/startup), not silently in playtesting.
- Headless harness green; `run_graphical.py` plays a full VS_AI game with the
  new unit selectable, animating, sounding, and showing help correctly.
