# GRAYMAN: The Immutable Anomaly

## Core Identity
A hybridized entity existing outside normal laws of reality - part alien, part elderly human. GRAYMAN stands resolute against forces that affect others, manipulating space-time while remaining unchanged himself.

## Base Stats
- **Attack Range**: 5 (Long-range attacker)
- **Movement**: 2 (Slower base movement compensated by teleportation)
- **Default Attack**: Weak but long-range

## Passive Ability
**Stasiality**: "Cannot have his stats changed or be displaced."
- Immune to buffs, debuffs, and forced movement effects
- Not affected by terrain bonuses or penalties
- Cannot be trapped, thrown, or pulled
- Represents his fixed nature in an otherwise changeable universe

## Active Abilities

### 1. Delta Config
"Teleport to any unoccupied tile on the map that isn't a pillar or furniture."
- Unlimited range repositioning
- No line-of-sight restrictions
- Leaves a brief ripple effect in space-time at departure/arrival points
- Cooldown: 4 turns

### 2. Estrange
"Fire a beam up to 5 tiles away that partially phases the target out of normal spacetime. Target becomes semi-transparent and receives -1 to all actions permanently."
- Long-range control ability that weakens effectiveness without changing stats
- Visually causes target to become partially transparent/grayscale
- Affected units appear to glitch/stutter when moving
- Cooldown: 3 turns

### 3. Græ Exchange
"GRAYMAN taps his cane on the ground, creating a faint duplicate of himself at his current position. He may then use Delta Config to teleport away. The echo remains for 2 turns and can perform basic attacks but cannot move or use abilities. If destroyed, it deals 3 damage to all adjacent units."
- Creates a visibly older duplicate at current position
- Echo has same attack range but half damage
- Echo has 5 HP and cannot be healed
- Echo appears hunched over with a cane and glowing eyes
- Cooldown: 5 turns

## Visual Design
- Appears as a tall, thin humanoid with grayish skin
- Wears a simple dark robe with subtle temporal symbols
- Head is somewhat elongated with large, completely black eyes
- Walks with a slight stoop and occasionally uses an ornate cane
- Voice has both electronic distortion and elderly quaver
- Attacks manifest as subtle distortions in reality rather than physical projectiles

## Tactical Role
Control specialist with unparalleled mobility. GRAYMAN excels at hit-and-run tactics, map control, and disruption rather than direct damage. His immunity to status effects makes him exceptionally reliable in chaotic situations.

## Implementation Notes
- Will need special handling for Stasiality passive to ignore all stat modifications
- Teleportation requires validation of destination tiles
- Exchange ability requires tracking a temporary unit with limited functionality
- Estrange needs effect visualization and stat tracking