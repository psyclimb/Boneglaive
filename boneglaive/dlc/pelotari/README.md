# PELOTARI - DLC Unit

**Version**: 1.0.0
**Complexity**: ★★★★★ (5 Glaives)
**Role**: Burst Damage / Disabler / Displacer

## Overview

The PELOTARI is a high-skill ranged specialist inspired by jai alai (Basque pelota). He wields a frequency-modulating cesta to launch ricocheting ball projectiles with unique physics-based mechanics.

## Stats

- **HP**: 18
- **Attack**: 4
- **Defense**: 1
- **Movement**: 4
- **Range**: 4 (base), 6 (with Riposte buff)
- **Symbol**: J

## Abilities

### Passive: Riposte
- Grants +2 attack range
- Refreshes every 3 turns
- When knocked off: Converts to 120° spread shot (6 balls, 4 damage each)
- Immune to buff theft (converts to spread shot instead)

### Skill 1: Poach (Cooldown: 3)
- Knock buff off enemy unit
- Buff becomes steal-able ball projectile
- Random buff selection if multiple buffs present
- Follows ricochet/phase mode physics

### Skill 2: Backhand (Cooldown: 4)
- Counter stance for entire turn
- Reflects enemy attacks/skills back as ball projectiles
- Only catches first attack per turn
- Ball uses ricochet/phase mode

### Skill 3: Cannonball (Cooldown: 6)
- Massive ball nuke
- 8 damage + knockback 3-4 tiles
- +4 slam damage if target hits terrain
- Launches furniture 3-4 tiles (deals 4 damage to units hit)
- Can reposition furniture on map

### Toggle: Ricochet / Phase Mode (Free Action)
- **Ricochet Mode**: Balls bounce once off terrain (angle of incidence)
- **Phase Mode**: Balls pass through terrain, only hit units
- Affects all ball projectiles
- Uses frequency modulation technology

## Installation

1. Extract this folder to `boneglaive/dlc/`
2. Ensure folder name is `pelotari` (lowercase)
3. Game will auto-discover on next startup

## Files

- `__init__.py` - Plugin registration
- `unit_config.json` - Stats and configuration
- `skills.py` - All ability implementations
- `physics.py` - Ball trajectory calculations
- `assets/` - Sprites, animations, sounds (to be added)

## Mechanics

### Ball Physics
- All projectiles use chess distance for trajectories
- Ricochet mode: Bounces once using angle of incidence
- Phase mode: Passes through terrain until hitting unit or map edge
- Spread shot: 120° cone, 6 balls, unlimited range

### Frequency Modulation
All terrain/furniture exists at specific molecular resonant frequencies. The PELOTARI's cesta contains a frequency modulator that synchronizes or desyncs projectiles with this frequency, allowing balls to either interact with terrain (ricochet) or phase through it.

## Balance

- **Strengths**: Long range, buff control, displacement, high burst damage
- **Weaknesses**: Low HP (18), low defense (1), high skill floor
- **Counters**: High-mobility rushers, long-range snipers, immunity effects

## Thematic Elements

- **Jai Alai Inspiration**: Traditional Basque pelota sport
- **Cesta**: Wicker throwing basket with integrated tech
- **Frequency Tuner**: Device on grip/wrist for toggling modes
- **Athletic Precision**: Skill-based trajectory mastery

## Development Status

- [x] Core skills implemented
- [x] Ball physics system
- [x] Toggle mechanic
- [ ] Graphical assets
- [ ] Sound effects
- [ ] Animation sequences
- [ ] Full playtesting

## See Also

- `PELOTARI_help.md` - Complete unit help page
- `DLC_CREATION_GUIDE.md` - How to create DLC units

---

**Author**: Boneglaive Team
**Last Updated**: 2025-12-13
