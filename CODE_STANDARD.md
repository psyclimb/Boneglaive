# Boneglaive — Code Standard

Audit checklist for code cleanliness. Point Claude here: "audit against CODE_STANDARD.md"

---

## 1. Dead Code

- No unused imports
- No unreachable branches or dead `elif`/`else`
- No commented-out code (delete it, git has history)
- No unused variables, methods, or classes
- No leftover scaffolding (empty methods, placeholder returns, TODO stubs)
- No bare `pass` statements before real code (debug artifacts)

## 2. Single Responsibility

- New files should own one concept
- Classes don't reach into each other's internals — use methods
- No god methods — if a method does 3 unrelated things, split it
- Existing large files (engine.py, renderer.py) are exempt from splitting but new code added to them should be kept focused

## 3. Data Flow

- Game state lives in `Game` (engine.py) — renderers read, never mutate directly
- `GameStateAdapter` bridges game logic to graphical renderer — the only data path
- Events flow through `EventManager` with typed `EventType` values
- Skill execution: `can_use()` → `use()` → `execute()` — no shortcuts
- Status effects initialized in `Unit.__init__`, not created dynamically via `setattr`

## 4. Consistency

- Coords are always `(y, x)` = `(row, col)`, grid access is `map[y][x]`
- Unit positions stored as `.y`, `.x` — no tuples for position storage
- Distance metric: Chebyshev (chess distance) — diagonal = 1 step
- `hasattr` guard before checking dynamic status effects
- Skill classes expose: `can_use()`, `use()`, `execute()`, `apply_passive()`, `tick_cooldown()`
- Damage formula: `max(1, ATK - DEF) - PRT`
- Config key for game mode: `game_mode` (values: `single`, `local`, `vs_ai`)

## 5. Architecture Boundaries

- Game engine (`boneglaive/game/`) is headless — no pygame, no curses, no rendering
- AI (`boneglaive/ai/`) reads game state and sets unit targets — never calls rendering code
- The graphical layer interacts with the game through `MultiplayerManager` for turn flow

## 6. No Overengineering

- No abstractions for one-off operations
- No config for things that aren't configurable
- No wrapper methods that just forward calls without adding logic
- No defensive checks for impossible states (trust internal code)
- Three similar lines > premature abstraction

## 7. Constants & Magic Numbers

- Named constants in `constants.py` for anything used in 2+ files
- Skill-specific values (damage, cooldown, range) as class attributes or named locals
- No inline magic numbers in game logic

## 8. Naming

- Files: `snake_case.py`
- Classes: `PascalCase`
- Methods/vars: `snake_case`
- Private: `_prefix` for internal-only methods and fields
- Constants: `UPPER_SNAKE` for module-level and class-level
- Event types: `PascalCase` enum values (`EventType.GAME_OVER`)
- Unit types: `UPPER_SNAKE` enum values (`UnitType.GLAIVEMAN`)
- Established abbreviations: `hp`, `gp`, `prt`, `ui`, `ai`, `cd`, `dy/dx`

## 9. Docstrings & Comments

- One-line module docstring at top of every `.py` file
- No method docstrings unless the behavior is non-obvious
- No inline comments restating what code does — only *why*
- No stale comments referencing removed features or old behavior

## 10. Version & Config Hygiene

- `__version__` in `boneglaive/__init__.py` is the single source of truth
- Version strings in UI, setup.py, and CI must match or reference it
- No stale config keys or enum values for removed features
- Config.json at project root is the bundled default; user config is in `~/.config/boneglaive/`
