# Boneglaive

**BETA VERSION 0.8.4** - Core gameplay complete, some features in development

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

## License
See LICENSE file for details.