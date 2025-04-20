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

## Common Issues and Prevention

### Multiplayer Turn Handling
- Both game.current_player and multiplayer.current_player must stay in sync
- Local multiplayer should allow control of whichever player is active
- UI should reflect current player at all times
- Any code that checks player ownership should consider local multiplayer mode

### UI Updates
- Always redraw the board after state changes
- Keep message log and chat system active in local multiplayer

## Development Workflow

### Testing Multiplayer
1. Update config.json to set `"network_mode": "local"`
2. Run with `python -m boneglaive.main --mode local --skip-menu`
3. Verify turn switching, unit control, and UI updates

### Debug Tools
- 'd' key shows unit positions
- 'D' toggles debug mode
- Message log provides game event history

## Renderer Abstraction

- All rendering should use the RenderInterface abstraction
- Game logic should never directly call rendering functions
- Coordinate translations should use the coordinates utility
- Asset references should use the AssetManager
- Input handling should use the InputHandler's logical actions
- Configuration changes should persist using ConfigManager

## UI Components

### Message Log
- Displays game events, combat outcomes, and player messages
- Toggle visibility with 'l' key
- Player messages are color-coded (Player 1: green, Player 2: blue)
- Combat messages indicate which player's units are involved

### Help Screen
- Access with '?' key
- Displays all available controls and their functions
- Press '?' again to return to game

### Chat System
- Press 'r' key to enter chat mode
- Type message and press Enter to send
- Messages appear in message log with player-specific colors
- Chat mode automatically activates message log if hidden
- Escape key cancels chat input

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

### Local Multiplayer
- Game supports "hot seat" style local multiplayer where players take turns
- Player switching occurs when ending turn with 'e' key
- UI header shows "Player X's Turn" to indicate current player
- Both players use the same computer, controlling their respective units
- Start with: `python -m boneglaive.main --mode local --skip-menu`

### LAN Multiplayer Guidelines
- Test multiplayer features on actual networks, not just localhost
- Add simple game discovery for finding LAN games
- Implement basic connection status indicators in UI
- Keep synchronization messages small and efficient 
- Add timeout handling for network operations
- Log network events for debugging connection issues
- Consider latency when designing game mechanics

### Network Architecture
- Abstraction layer in `network_interface.py` supports multiple connection types
- Local implementation in `local_multiplayer.py`
- LAN implementation in `lan_multiplayer.py`
- Player state managed in `multiplayer_manager.py`

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

## Continuity Guidelines After /compact

- On resuming, start with a quick reference to CLAUDE.md to restore context
- Include these elements in the first message after /compact:
  1. The specific feature or issue being worked on
  2. Key files relevant to the current task (1-3 most important ones)
  3. Any immediate next steps planned before the /compact
- Avoid lengthy explanations of what was done before - stay focused on next steps
- Use action-oriented language: "We need to implement X" rather than "We were working on X"
- For complex topics, reference specific sections in CLAUDE.md rather than re-explaining
- If picking up a refactoring task, mention only the specific files still needing attention
- Keep task descriptions concise and targeted - prefer bullet points over paragraphs
- Avoid full file exploration when a directed search can locate relevant code sections
- Keep responses brief and to the point unless asked to elaborate
- Prefer single-sentence answers when possible and appropriate