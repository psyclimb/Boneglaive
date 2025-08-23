# Boneglaive2 🎯

A tactical turn-based combat game with dual rendering modes: classic terminal (curses) and modern graphical (pygame).

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