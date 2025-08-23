# CLAUDE.md - Boneglaive2 Development Guide

## Project Overview
Tactical turn-based combat game in Python using curses terminal UI. Features complex skill systems, multiplayer networking, and modular architecture.

**IMPORTANT**: Work with current codebase state only. Do not reference git history, past commits, or previous code versions unless explicitly requested by the user.

## Essential Architecture

### Core Structure
- `main.py` - Entry point with CLI args for different game modes
- `game/engine.py` - Central Game class managing state, turns, combat
- `game/units.py` - Unit class with stats, skills, status effects
- `game/skills/` - Modular skill system with registry pattern
- `networking/` - Abstract multiplayer interfaces with concrete implementations
- `ui/` - Component-based UI system with event-driven updates
- `renderers/curses_renderer.py` - Terminal rendering backend
- `utils/` - Config, events, assets, debugging utilities

### Key Patterns
- **Skills**: Base classes in `skills/core.py`, unit-specific modules, registry in `skills/registry.py`
- **UI Components**: Modular components in `ui/ui_components.py` with clear separation
- **Networking**: Abstract `NetworkInterface` with mode-specific implementations
- **Configuration**: JSON-based config with dataclasses in `utils/config.py`

## Development Workflows

### Running the Game
```bash
PYTHONPATH=/path/to/boneglaive2 python3 boneglaive/main.py [--single-player|--local-mp|--lan-host|--lan-client|--vs-ai]
```

### Testing
```bash
python3 boneglaive_test.py  # Integration tests for maps and game mechanics
```

### Common Tasks
- **Add new unit type**: Create skill module in `game/skills/`, update `registry.py`, add to `units.py`
- **Add new skill**: Inherit from `ActiveSkill`/`PassiveSkill` in appropriate unit module
- **Modify UI**: Extend components in `ui/ui_components.py` or create new component
- **Add terrain**: Update `map.py` with new terrain type and behaviors
- **Debug**: Use logging in `utils/debug.py`, enable debug overlays with CLI flags

## Key Design Decisions
- **Turn-based engine**: Players alternate, actions resolved in sequence
- **Greek letter unit IDs**: Alpha, Beta, Gamma, etc. for unit identification
- **Status effects**: Complex system with timers, immunities, interactions
- **Event system**: Decoupled communication via `utils/event_system.py`
- **Double-buffered rendering**: Reduces terminal flicker in curses
- **JSON serialization**: For network messages and save data

## Dependencies
- Python 3.x with curses, json, socket, threading (standard library only)
- No external package dependencies

## Git Repository Management
**IMPORTANT**: This project has been merged into the original boneglaive repository. All future commits should be pushed to:
- Repository: https://github.com/psyclimb/Boneglaive.git
- Remote name: `original`
- **DO NOT** push to the boneglaive2 repository anymore

Use these commands for git operations:
```bash
git push original main  # Push to main boneglaive repository
git fetch original      # Fetch from main repository
```

## File Priorities for AI Development
1. `game/engine.py` - Core game logic
2. `game/skills/core.py` - Skill base classes
3. `game/units.py` - Unit behavior and stats
4. `ui/ui_components.py` - UI component system
5. `utils/config.py` - Configuration management
6. `game/skills/registry.py` - Skill-to-unit mappings

## Current Limitations
- No formal unit testing framework
- Experience/leveling system disabled
- AI implementation is basic (`ai/simple_ai.py`)
- Limited animation system