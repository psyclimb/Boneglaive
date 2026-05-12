# Boneglaive Sound Files

This directory contains all sound effects and music for Boneglaive.

## Directory Structure

```
sounds/
├── skills/         # Skill and ability sound effects
├── impacts/        # Hit effects, explosions, etc.
├── ui/            # Menu and interface sounds
└── music/         # Background music tracks
```

## File Naming Convention

All sound files should be:
- **Format**: WAV (`.wav`)
- **Naming**: lowercase with underscores (e.g., `estrange.wav`, `hit_critical.wav`)
- Matched to entries in `boneglaive/graphical/sound_registry.py`

## Adding New Sounds

1. Place your `.wav` file in the appropriate category folder
2. Update `sound_registry.py` with the mapping:
   ```python
   SKILL_SOUNDS = {
       "YOUR_SKILL_NAME": "your_filename",  # without .wav extension
       ...
   }
   ```
3. The sound will automatically be available in-game

## Example: Adding a Sound for ESTRANGE skill

1. Create/obtain `estrange.wav`
2. Place it in `sounds/skills/estrange.wav`
3. The registry already maps `"ESTRANGE"` → `"estrange"`
4. Play in animations: `sound_manager.play("estrange", category="skills")`

## Testing Sounds

Use the test sound system:
```bash
# Place test_sound1.wav in sounds/skills/ folder
# Use GRAYMAN's Estrange skill in-game
```

## Volume Levels

Adjust volume per category via SoundManager:
- Master volume: 0.0 - 1.0
- Skills volume: 0.0 - 1.0
- Impacts volume: 0.0 - 1.0
- UI volume: 0.0 - 1.0
- Music volume: 0.0 - 1.0

## Current Status

Sound system is implemented but requires sound files to be added.
All skill mappings are defined in `sound_registry.py`.
