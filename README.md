# Boneglaive

**BETA VERSION 0.7.2a** - Core gameplay complete, some features in development

**Linux & BSD Terminal Gaming** - A tactical turn-based combat game designed for *nix terminal environments using ncurses.

> **Platform Support**: Boneglaive is designed for Linux and BSD systems, taking full advantage of native terminal capabilities.

> **For Developers & Testers**: See [Contributing](#-contributing) section below for development setup and testing guidelines.

## Installation

### Linux & BSD Setup
Boneglaive requires Python 3.8+ and uses the native curses library available on Linux and BSD systems:

```bash
# Ensure you have Python 3.8 or later
python3 --version

# No additional dependencies needed for core gameplay!
# Run directly from your Boneglaive directory:
python3 -m boneglaive.main
```


### Project Structure
- `boneglaive/` - Main game code
  - `renderers/` - Terminal rendering system
  - `game/` - Core game logic and skills
  - `ui/` - User interface components

## Features

- **Pure Terminal**: Authentic ncurses terminal interface
- **Native Terminal**: Optimized for Linux and BSD environments
- **Complex Combat**: Unit skills, status effects, terrain
- **Singleplayer**: Singleplayer vs bots
- **Multiplayer**: Hotseat multiplayer
- **Zero Dependencies**: Pure Python standard library

## Controls

- **Arrow Keys**: Movement
- **Enter/Space**: Select/Confirm
- **m**: Move mode
- **a**: Attack mode  
- **s**: Skill mode
- **t**: End turn
- **c**: Cancel action
- **?**: Help
- **l**: Toggle message log
- **L**: Toggle full message log
- **Tab**: Cycle through units
- **Shift+Tab**: Cycle backwards through units
- **p**: Activate appraiser anchor

## ⚠️ Development Status - BETA 0.7.1

**Text Mode**: Fully functional and polished - recommended for play
**Graphical Mode**: Incomplete - use text mode for best experience
**Multiplayer**: Code exists but UI not accessible (single-player only currently)

This beta version represents solid, playable core gameplay with some major features still in development toward 1.0 release.

## 🤝 Contributing

### For Developers
1. **Setup**: Clone the repository and run `python install.py`
2. **Code Style**: Follow PEP 8, use 4-space indentation
3. **Testing**: Test all game modes before submitting PRs
4. **Documentation**: Update CLAUDE.md for significant changes

### For Testers
1. **Bug Reports**: Use GitHub issues with detailed steps to reproduce
2. **Test Coverage**: Try different unit combinations, skills, edge cases
3. **Performance**: Note any lag, crashes, or display issues
4. **Platforms**: Test on different OS if possible (Windows/macOS/Linux)

### Development Commands
```bash
# Run tests
python boneglaive_test.py

# Build executable (for testing distribution)
python build_executable.py

# Clean cache files
find . -name "__pycache__" -exec rm -rf {} +
```

### Known Issues & Limitations
- Graphical mode is incomplete - use text mode
- Multiplayer code exists but not accessible via UI (single-player only currently)
- Terminal resizing can cause display glitches in text mode
- AI difficulty is currently basic
- Save/load functionality not yet implemented
- Limited animation system

## 📄 License
See LICENSE file for details.