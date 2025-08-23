# Boneglaive 🎯

A tactical turn-based combat game with dual rendering modes: classic terminal (curses) and modern graphical (pygame).

> **For Developers & Testers**: See [Contributing](#-contributing) section below for development setup and testing guidelines.

## 🚀 Quick Start (Choose One)

### Option 1: Automatic Installation (Recommended)
```bash
python install.py
```
This automatically installs all dependencies including pygame.

### Option 2: Manual Installation
```bash
pip install pygame
# On Windows, also install:
pip install windows-curses
```

### Option 3: Using pip with requirements
```bash
pip install -r requirements.txt
```

## 🎮 Running the Game

### Graphical Mode (Recommended)
1. Set `"display_mode": "graphical"` in `config.json`
2. Run: `python boneglaive/main.py`

### Text Mode
1. Set `"display_mode": "text"` in `config.json` 
2. Run: `python boneglaive/main.py`

## 🔧 Game Modes

- **Single Player**: `--single-player`
- **Local Multiplayer**: `--local-mp` 
- **LAN Host**: `--lan-host`
- **LAN Client**: `--lan-client`
- **VS AI**: `--vs-ai`

## 📦 For Developers

### Create Standalone Executable
```bash
python build_executable.py
```
This creates a single executable file that users can run without installing Python or pygame.

### Project Structure
- `boneglaive/` - Main game code
  - `renderers/` - Cross-platform rendering (curses + pygame)
  - `game/` - Core game logic and skills
  - `ui/` - User interface components
  - `networking/` - Multiplayer support

## 🎯 Features

- **Dual Rendering**: Terminal-based and graphical modes
- **Cross-Platform**: Windows, macOS, Linux
- **Complex Combat**: Unit skills, status effects, terrain
- **Multiplayer**: Local and network play
- **No External Dependencies**: Pure Python + pygame

## ⚡ Controls

- **Arrow Keys**: Movement
- **Enter/Space**: Select/Confirm
- **M**: Move mode
- **A**: Attack mode  
- **S**: Skill mode
- **?**: Help

## 🐛 Troubleshooting

**Pygame not found?**
```bash
python install.py
```

**Windows curses issues?**
```bash
pip install windows-curses
```

**Can't run the game?**
Make sure you have Python 3.8+ and run from the project root directory.

## ⚠️ Development Status

**Text Mode**: Fully functional and recommended for play
**Graphical Mode**: Unfinished - use text mode for best experience

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