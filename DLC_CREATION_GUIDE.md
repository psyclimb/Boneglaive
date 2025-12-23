# Boneglaive DLC Unit Creation Guide

## Overview

This guide explains how to create DLC units for Boneglaive. DLC units are modular, drop-in packages that extend the game with new playable characters without modifying core game files.

**Status**: Work in Progress - Plugin system under development

---

## DLC Package Structure

Each DLC unit is contained in its own directory under `boneglaive/dlc/`:

```
boneglaive/dlc/
└── pelotari/                    # DLC unit name (lowercase)
    ├── __init__.py              # Plugin registration and exports
    ├── unit_config.json         # Unit metadata and stats
    ├── skills.py                # Skill implementations
    ├── physics.py               # Custom physics/mechanics (optional)
    ├── assets/                  # All visual/audio assets
    │   ├── sprites/             # Graphical mode sprites
    │   │   ├── idle.png
    │   │   ├── attack.png
    │   │   ├── move.png
    │   │   └── death.png
    │   ├── animations/          # Skill animation frames
    │   │   ├── skill1_frames/
    │   │   ├── skill2_frames/
    │   │   └── skill3_frames/
    │   ├── projectiles/         # Projectile sprites
    │   │   ├── ball_normal.png
    │   │   └── ball_phased.png
    │   └── sounds/              # Sound effects (optional)
    │       ├── attack.wav
    │       ├── skill1.wav
    │       └── toggle.wav
    └── README.md                # Unit documentation
```

---

## 1. Unit Configuration (`unit_config.json`)

Defines the unit's base properties, stats, and visual representation.

```json
{
  "unit_name": "PELOTARI",
  "unit_id": "pelotari",
  "display_name": "PELOTARI",
  "description": "Jai alai specialist with ricochet ball mechanics",
  "complexity": 5,
  "role": "Burst Damage / Disabler / Displacer",

  "stats": {
    "hp": 18,
    "attack": 4,
    "defense": 1,
    "move_range": 4,
    "attack_range": 4
  },

  "ascii": {
    "symbol": "P",
    "attack_effect": "o",
    "colors": {
      "player1": 3,
      "player2": 4
    }
  },

  "graphical": {
    "sprite_size": [32, 32],
    "animation_fps": 12,
    "sprite_sheets": {
      "idle": "assets/sprites/idle.png",
      "attack": "assets/sprites/attack.png",
      "move": "assets/sprites/move.png",
      "death": "assets/sprites/death.png"
    }
  },

  "gp_eligible": true,
  "version": "1.0.0",
  "author": "Boneglaive Team"
}
```

---

## 2. Skills Implementation (`skills.py`)

All passive and active skills for the unit.

### Required Structure

```python
#!/usr/bin/env python3
"""
Skills for PELOTARI DLC unit.
"""

from typing import Optional, TYPE_CHECKING
from boneglaive.game.skills.core import PassiveSkill, ActiveSkill, TargetType

if TYPE_CHECKING:
    from boneglaive.game.units import Unit
    from boneglaive.game.engine import Game


class PassiveSkillName(PassiveSkill):
    """Passive skill description."""

    def __init__(self):
        super().__init__(
            name="Skill Name",
            key="K",
            description="Skill description for UI"
        )

    def apply_passive(self, user: 'Unit', game: Optional['Game'] = None, ui=None) -> None:
        """Apply passive effects."""
        pass


class ActiveSkillName(ActiveSkill):
    """Active skill description."""

    def __init__(self):
        super().__init__(
            name="Skill Name",
            key="K",
            description="Skill description",
            target_type=TargetType.ENEMY,  # or ALLY, AREA, SELF
            cooldown=3,
            range_=4
        )

    def can_use(self, user: 'Unit', target_pos: Optional[tuple] = None,
                game: Optional['Game'] = None) -> bool:
        """Check if skill can be used."""
        if not super().can_use(user, target_pos, game):
            return False
        # Custom validation logic
        return True

    def use(self, user: 'Unit', target_pos: Optional[tuple] = None,
            game: Optional['Game'] = None) -> bool:
        """Queue skill for execution."""
        if not self.can_use(user, target_pos, game):
            return False

        user.skill_target = target_pos
        user.selected_skill = self

        if game:
            user.action_timestamp = game.action_counter
            game.action_counter += 1

        self.current_cooldown = self.cooldown
        return True

    def execute(self, user: 'Unit', target_pos: tuple, game: 'Game', ui=None) -> bool:
        """Execute skill during combat phase."""
        # Skill logic here
        return True


# Export all skills
PASSIVE_SKILL = PassiveSkillName
ACTIVE_SKILLS = [
    ActiveSkillName,
    # ... more active skills
]
```

---

## 3. Plugin Registration (`__init__.py`)

Registers the DLC unit with the game's plugin system.

```python
#!/usr/bin/env python3
"""
PELOTARI DLC Plugin
"""

from .skills import PASSIVE_SKILL, ACTIVE_SKILLS
from pathlib import Path
import json

# Load unit configuration
config_path = Path(__file__).parent / "unit_config.json"
with open(config_path, 'r') as f:
    UNIT_CONFIG = json.load(f)

# Plugin metadata
PLUGIN_NAME = "pelotari"
PLUGIN_VERSION = "1.0.0"
REQUIRES_GAME_VERSION = "0.1.0"

# Export unit class for registration
def register_unit(game):
    """
    Called by game to register this DLC unit.

    Args:
        game: Game instance to register with

    Returns:
        dict: Unit registration data
    """
    return {
        'config': UNIT_CONFIG,
        'passive_skill': PASSIVE_SKILL,
        'active_skills': ACTIVE_SKILLS,
        'assets_path': Path(__file__).parent / 'assets'
    }


__all__ = ['UNIT_CONFIG', 'PASSIVE_SKILL', 'ACTIVE_SKILLS', 'register_unit']
```

---

## 4. Custom Physics/Mechanics (Optional)

For units with unique mechanics (like PELOTARI's ball physics), create a separate module:

```python
#!/usr/bin/env python3
"""
Ball physics system for PELOTARI.
"""

def calculate_trajectory(start_pos, target_pos, mode='ricochet'):
    """
    Calculate ball trajectory with ricochet or phase mechanics.

    Args:
        start_pos: (y, x) starting position
        target_pos: (y, x) target position
        mode: 'ricochet' or 'phase'

    Returns:
        list: Path of tiles the ball travels through
    """
    pass


def calculate_bounce(impact_pos, incoming_vector, terrain_type):
    """
    Calculate bounce angle using angle of incidence.

    Args:
        impact_pos: (y, x) where ball hits
        incoming_vector: (dy, dx) direction of travel
        terrain_type: Type of terrain hit

    Returns:
        tuple: New direction vector (dy, dx)
    """
    pass
```

---

## 5. Asset Requirements

### ASCII Mode
- **Symbol**: Single character representing the unit
- **Attack Effect**: Character shown during attacks
- **Status Icons**: Characters for custom status effects

### Graphical Mode

#### Sprite Sheets
- **Idle**: Looping idle animation
- **Attack**: Attack animation
- **Move**: Walking/movement animation
- **Death**: Death/defeat animation

**Format**: PNG, transparent background
**Size**: 32x32 pixels per frame (configurable)

#### Animation Frames
Each skill needs its own animation sequence:
- Frame-by-frame PNG files
- Numbered sequentially (frame_001.png, frame_002.png, etc.)
- Same size as unit sprites

#### Projectiles
- Separate sprites for projectiles
- Variants for different modes (normal vs phased, etc.)

#### Sound Effects (Optional)
- **Format**: WAV or OGG
- **Sample Rate**: 44.1kHz recommended
- **Channels**: Mono or stereo

---

## 6. Testing Your DLC

### Loading the DLC

1. Place your DLC folder in `boneglaive/dlc/`
2. Game will auto-discover on startup
3. Check console for loading messages

### Test Checklist

- [ ] Unit appears in unit selection
- [ ] Stats load correctly
- [ ] Passive skill applies on spawn
- [ ] All active skills can be selected
- [ ] Skills execute without errors
- [ ] ASCII symbols display correctly
- [ ] Graphical sprites load and animate
- [ ] Sound effects play (if included)
- [ ] Unit works in both single and multiplayer

---

## 7. Distribution

### Package Format

DLC units can be distributed as:
1. **Folder**: Direct `dlc/unit_name/` directory
2. **ZIP Archive**: Users extract to `dlc/` folder
3. **Git Repository**: Users clone into `dlc/` folder

### File Naming Conventions

- Use lowercase with underscores: `unit_name`
- Config file must be `unit_config.json`
- Main registration file must be `__init__.py`
- Skills file must be `skills.py`

### Version Compatibility

Specify minimum game version in `unit_config.json`:
```json
"requires_game_version": "0.1.0"
```

---

## 8. Example: PELOTARI DLC

See `boneglaive/dlc/pelotari/` for a complete reference implementation showcasing:

- Complex passive with buff mechanics
- Multiple active skills with unique targeting
- Custom physics system (ball ricochets)
- Toggle mechanic (4th action menu item)
- Full ASCII and graphical asset integration
- Advanced animations and particle effects

---

## 9. Best Practices

### Performance
- Keep skill calculations efficient
- Cache frequently-used values
- Minimize file I/O during gameplay

### Compatibility
- Don't modify core game files
- Use only public APIs from `boneglaive.game.skills.core`
- Test with different unit combinations

### Documentation
- Include detailed README.md in DLC folder
- Document all custom mechanics
- Provide balance rationale for stats

### Assets
- Optimize image sizes
- Use appropriate formats (PNG for sprites, WAV for sounds)
- Include attribution for any third-party assets

---

## 10. Plugin System API

### Core Imports

```python
from boneglaive.game.skills.core import (
    PassiveSkill,
    ActiveSkill,
    TargetType
)
from boneglaive.utils.message_log import message_log, MessageType
from boneglaive.utils.constants import UnitType  # For type checking only
```

### Available Target Types
- `TargetType.ENEMY` - Single enemy unit
- `TargetType.ALLY` - Single ally unit
- `TargetType.AREA` - Area target (ground or unit)
- `TargetType.SELF` - Self-targeting skill

### Message Logging

```python
from boneglaive.utils.message_log import message_log, MessageType

# Log ability usage
message_log.add_message(
    f"{user.get_display_name()} uses {self.name}",
    MessageType.ABILITY,
    player=user.player
)

# Log combat
message_log.add_combat_message(
    attacker_name=user.get_display_name(),
    target_name=target.get_display_name(),
    damage=damage_dealt,
    ability=self.name,
    attacker_player=user.player,
    target_player=target.player
)
```

---

## Support

For questions or issues with DLC creation:
- Check existing DLC implementations in `boneglaive/dlc/`
- Review core skill files in `boneglaive/game/skills/`
- Open an issue on the Boneglaive repository

---

**Last Updated**: 2025-12-13
**Plugin System Version**: 1.0.0 (In Development)
**Compatible Game Version**: 0.1.0+
