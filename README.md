# Boneglaive

**VERSION 1.0.0** - Tactical Turn-Based Combat Game

A strategic turn-based combat game featuring unit abilities, status effects, and tactical positioning. Available in both terminal (ASCII) and graphical (pygame) versions.

> **Platform Support**: Linux, BSD, macOS, and Windows

## Quick Start

### Graphical Version (Recommended)
```bash
# Install pygame (if not already installed)
pip install pygame

# Run the game
python run_graphical.py
```

### ASCII Terminal Version
```bash
# No dependencies needed - uses Python standard library
python -m boneglaive.main
```

## Features

- **Two Game Versions**: Modern graphical UI or classic terminal interface
- **GP Scoring System**: Race to 7 GP - units respawn after death
- **Tactical Combat**: Grid-based movement, ranged attacks, area effects
- **10+ Unique Units**: Each with 4 active skills and 1 passive ability
- **Multiple Game Modes**:
  - Single player vs AI
  - Local multiplayer (hotseat)
  - LAN multiplayer
- **Status Effects**: Debuffs, buffs, crowd control, damage over time
- **DLC System**: Expandable with custom units

## Controls

### Graphical Version
- **Mouse**: Click to select units, move, attack, use skills
- **1-4, Q-R**: Activate skills by hotkey
- **E**: Execute turn
- **ESC**: Cancel/deselect

### ASCII Terminal Version
- **Arrow Keys**: Navigate
- **Enter/Space**: Select/Confirm
- **m**: Move mode
- **a**: Attack mode
- **s**: Skill mode (1-4, Q-R to select)
- **r**: Respawn menu
- **t**: End turn
- **c**: Cancel action
- **l**: Toggle message log
- **L**: Expand message log
- **Tab**: Cycle units
- **?**: Help

## Game Modes

```bash
# Graphical version (interactive menu)
python run_graphical.py

# ASCII version - vs AI
python -m boneglaive.main --mode vs_ai

# ASCII version - local multiplayer
python -m boneglaive.main --mode local

# ASCII version - LAN host
python -m boneglaive.main --mode lan_host --port 7777

# ASCII version - LAN client
python -m boneglaive.main --mode lan_client --server 192.168.1.100 --port 7777
```

## Requirements

**Graphical Version:**
- Python 3.8+
- pygame 2.0+

**ASCII Version:**
- Python 3.8+ with curses (included on Linux/BSD/macOS)
- Terminal with UTF-8 support and Greek character rendering

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

See the [LICENSE](LICENSE) file for full details.

**In brief**: You are free to use, modify, and distribute this software, but any distributed modifications must also be released under GPL-3.0 and include source code.