# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run game: `python -m boneglaive.main`
- Run with debug: `python -m boneglaive.main --debug --log-file --overlay`
- Run tests: N/A (use test mode inside the game with 't' key)
- Debug: 
  - Basic: Use 'd' key inside game to show unit positions
  - Advanced: Use 'D' key to toggle debug mode, 'O' for overlay, 'P' for performance tracking

## Code Style Guidelines

- Indentation: 4 spaces
- Line length: ~80 characters
- Imports: Standard library first, group related imports
- Naming:
  - Classes: CamelCase (Game, Unit, GameUI)
  - Methods/Functions: snake_case (is_alive, get_unit_at)
  - Constants: UPPERCASE (WIDTH, HEIGHT, MAX_UNITS)
- Error handling: Use conditional checks for validation
- Documentation: Add docstrings for complex functions
- Type handling: Use Enum for type definitions

## Project Structure

The project is organized in a modular structure:
```
boneglaive/
├── __init__.py
├── main.py           # Entry point
├── game/
│   ├── __init__.py
│   ├── engine.py     # Game logic (Game class)
│   ├── units.py      # Unit definitions
│   └── animations.py # Animation logic
├── ui/
│   ├── __init__.py
│   └── game_ui.py    # UI handling (GameUI class)
├── renderers/
│   ├── __init__.py
│   └── curses_renderer.py # Text-based renderer implementation
├── networking/
│   ├── __init__.py
│   ├── network_interface.py # Abstract network interface
│   ├── local_multiplayer.py # Local multiplayer implementation
│   ├── lan_multiplayer.py   # LAN multiplayer implementation
│   ├── game_server.py       # Game server for LAN play
│   └── game_state_sync.py   # Game state synchronization
└── utils/
    ├── __init__.py
    ├── constants.py  # Game constants, enums
    ├── debug.py      # Debugging utilities
    ├── config.py     # Configuration management
    ├── coordinates.py # Coordinate system utilities
    ├── asset_manager.py # Asset management
    ├── input_handler.py # Input abstraction
    └── render_interface.py # Renderer abstraction
```

## Best Practices

- Single Responsibility: Each module should handle one aspect of the game
- Dependency Injection: Pass dependencies rather than creating them
- Configuration: Move hardcoded values to config files when possible
- Event System: Consider using event system for complex interactions
- Testing:
  - Add unit tests for game logic
  - Create test fixtures for common game states
- Documentation:
  - Add docstrings for all public functions/methods
  - Include examples in docstrings for complex functions
- Clean Code:
  - Keep functions small (under 20 lines when possible)
  - Use meaningful variable names
  - Avoid deep nesting
- Resource Management:
  - Add proper cleanup for curses
  - Handle window resizing gracefully

## Debugging Guidelines

- Use the debug system with appropriate levels:
  - Use `logger.debug()` for detailed tracing information
  - Use `logger.info()` for confirmation of normal events
  - Use `logger.warning()` for unexpected situations
  - Use `logger.error()` for error conditions
- Apply performance tracking to complex functions with `@measure_perf` decorator
- Use `game_assert()` for validation that shouldn't crash production code
- Add new features to debug overlay when appropriate
- Save game states for debugging using 'S' key in debug mode

## Renderer Abstraction

- All rendering should use the RenderInterface abstraction
- Game logic should never directly call rendering functions
- Coordinate translations should use the coordinates utility
- Asset references should use the AssetManager
- Input handling should use the InputHandler's logical actions
- Configuration changes should persist using ConfigManager

## Networking Architecture

- Use NetworkInterface for all network communications
- Support three game modes: single-player, local multiplayer, LAN multiplayer
- Follow these principles for multiplayer implementation:
  - Use the NetworkInterface to abstract connection details
  - Separate game logic from network code
  - Use GameStateSync for state synchronization between clients
  - Host acts as authoritative server for game state
  - Minimize network traffic by sending only changes
  - Use MessageType enum for consistent message handling
  - Always handle network errors gracefully
  - Provide fallback to local play if network disconnects

## Versioning

- Project is currently in conceptualization/POC stage
- Use descriptive commit messages to track development phases
- Consider semantic versioning (MAJOR.MINOR.PATCH) only after core gameplay is stable
- Focus on experimental features and rapid iteration
- Document significant design decisions in comments

## Token Optimization

- When viewing code: Use specific line ranges rather than reading entire file
- Search with GrepTool for specific functions instead of reading full file
- Use BatchTool for multiple related operations
- For animation functions, modify small sections rather than replacing entire function
- When compacting code:
  - Combine related constants into dictionaries/maps
  - Use list comprehensions instead of explicit loops where appropriate
  - Refactor long methods into smaller utility functions
  - Remove redundant validation when context guarantees safety
- When committing:
  - Group related changes in a single commit
  - Use targeted git diff with specific file paths instead of full diff
  - Include only essential context in commit analysis
  - Skip viewing unchanged files when staging