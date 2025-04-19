# Boneglaive

A turn-based tactical combat game built with Python and curses.

## Game Overview

Boneglaive is a tactical combat game where two players control units with different abilities on a grid battlefield. Units include warriors, archers, and mages, each with unique stats and attack ranges.

## Project Structure

The project is now organized into modules:
- `boneglaive/utils/constants.py` - Game constants and enums
- `boneglaive/game/units.py` - Unit class definition
- `boneglaive/game/engine.py` - Core game logic
- `boneglaive/game/animations.py` - Animation utilities
- `boneglaive/ui/game_ui.py` - User interface handling
- `boneglaive/main.py` - Entry point

## Running the Game

```bash
# Run the game normally
python -m boneglaive.main

# Run with debugging enabled
python -m boneglaive.main --debug --log-file --overlay
```

## Game Controls

### Basic Controls
- Arrow keys: Move cursor
- Enter: Select unit/confirm action
- m: Move selected unit
- a: Attack with selected unit
- e: End turn
- c: Clear selection
- t: Toggle test mode (allows controlling both players' units)
- q: Quit game

### Debug Controls
- d: Show unit positions
- D (Shift+D): Toggle debug mode
- O (Shift+O): Toggle debug overlay
- P (Shift+P): Toggle performance tracking
- S (Shift+S): Save game state to file (debug mode only)

## Development

This project is in conceptualization/proof-of-concept stage. See CLAUDE.md for development guidelines.