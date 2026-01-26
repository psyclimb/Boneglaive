# LANDSCAPER - Unit Concept (Work in Progress)

## Overview
A battlefield sculptor who terraforms the map, creates tempo for her team, and summons an unstoppable MOUND KING to dominate territorial control. She arranges terrain, furniture, and enemies into deadly patterns, then unleashes area-wide punishment through her summoned giant.

**Role:** Territory Control / Summoner / Tempo
**Difficulty:** **** (4 Glaives - High Complexity)

## Base Stats (Proposed)
- **HP:** TBD
- **Attack:** TBD
- **Defense:** TBD
- **Movement:** TBD
- **Range:** TBD
- **Symbol:** TBD

---

## Passive Skill

### EARTHMOVER (Passive) - *[Multiple variants under consideration]*

**Variant A: Pure Utility**
- LANDSCAPER can move through terrain as if it were passable
- No cooldown
- Effect: Provides positioning flexibility to navigate sculpted battlefields

**Variant B: Terrain Manipulation with Cooldown**
- Cooldown: 2 (reduced to 1 on consecrated ground)
- LANDSCAPER can move through terrain as if passable when off cooldown
- Effect when used: TBD (attack bonus? terrain recycling? trail creation?)

**Variant C: Bedrock Stance**
- LANDSCAPER gains +1 DEF for each piece of terrain within 2 tiles
- Effect: Makes her naturally tankier in sculpted areas

**Variant D: Fertile Ground**
- While MOUND KING is alive, LANDSCAPER gains +1 movement range
- Effect: Rewards keeping MOUND KING alive and encourages protection

*Designer Note: Variant A (pure utility) may fit best - she's already doing heavy lifting with active skills*

---

## Active Skills

### GROUND SWELL (Active) [Key: 1]
Creates a mound of earth at target location that reshapes the battlefield and summons a MOUND KING after a delay.

**Details:**
- **Type:** Active
- **Range:** TBD
- **Cooldown:** TBD
- **Effect:** Creates a mound that shoves all terrain and furniture on top of it to its edges
- **Emergence Time:** 2-3 turns (TBD)
- **Emergence Effect: "Buried Alive"** - When MOUND KING emerges, all enemies on the mound take 3 damage and become immobilized for 1 turn (cannot move, can still attack/skill)
- **Special:** The mound blocks movement while forming; terrain clustering at edges creates damage zones for MOUND KING's Landslide Step

---

### TOPIARY BREATH (Active) [Key: 2]
Forces all terrain, furniture, and enemies in a large cone into a specific pattern or arrangement. Enemy units are temporarily banished as topiaries.

**Details:**
- **Type:** Active
- **Range:** Large cone (dimensions TBD)
- **Cooldown:** TBD
- **Effect on Terrain/Furniture:** Forced into specific pattern/arrangement (exact pattern TBD)
- **Effect on Enemies:** Transformed into topiaries and removed from battlefield
- **Banishment Duration:** 2-3 turns (TBD - possibly shorter for enemies closer to LANDSCAPER?)
- **Special:** Creates predictable enemy positioning for MOUND KING's Landslide Step; major battlefield reset ability

---

### SCULPTOR'S FOUNDATION / EARTHEN CONSECRATION (Active) [Key: 3]
*[Name TBD]*

Marks ground with a consecration effect that accelerates ally cooldowns while they stand on it.

**Details:**
- **Type:** Active (Ground Effect)
- **Range:** TBD (placement range for the zone)
- **Zone Size:** 2x2, 3x3, or 4x4 (TBD)
- **Duration:** 2-3 turns (TBD) or indefinite?
- **Effect:** While allies stand on consecrated ground, their skill cooldowns tick down 1 additional turn per turn (effectively -1 cooldown to all skills)
- **Special:**
  - One-time aura effect - only works while standing on the ground
  - Skills with cooldown 2 become usable every turn while on ground
  - Best used to predict where battle will occur after MOUND KING emerges
  - Strong synergy with MOUND KING's Landslide Step (cooldown 1 → 0)

---

## MOUND KING (Summoned Unit)

### Overview
An unkillable giant that serves as a walking area denial zone. Not meant to be killed - functions as a timed territorial pressure tool.

### Stats (Proposed)
- **HP:** 40-50 (functionally unkillable)
- **Attack:** 3-4 (low damage output)
- **Defense:** 8-10 with PRT
- **Movement:** 1 (slow, lumbering)
- **Range:** Melee (TBD)
- **Duration:** 3 turns (dies automatically after 3 turns)

### Passive: LANDSLIDE STEP
Triggers when MOUND KING moves, dealing damage to all enemies adjacent to terrain within massive range.

**Details:**
- **Trigger:** When MOUND KING moves
- **Range:** 7x7 area around MOUND KING (map-wide coverage)
- **Damage:** Scales with distance moved
  - Move 1 tile → 1 damage to affected enemies
  - Move 2 tiles → 2 damage to affected enemies
  - Move 3 tiles → 3 damage to affected enemies
- **Target:** All enemies within 7x7 who are adjacent to terrain
- **Cooldown:** 1 (reduced to 0 on consecrated ground, allowing movement every turn)
- **Special:** Ground Swell clusters terrain at edges, creating damage corridors; Topiary Breath forces enemies into patterns near terrain

---

## Synergies & Combos

### The Full Combo:
1. **Ground Swell** - Create mound, cluster terrain at edges
2. **Sculptor's Foundation** - Place consecrated ground where MOUND KING will emerge
3. **MOUND KING emerges** - Buried Alive immobilizes camping enemies
4. **MOUND KING on buff** - Landslide Step activates every turn (cooldown 0)
5. **Topiary Breath** - Force enemies into patterns near terrain
6. **3-turn tempo window** - MOUND KING creates map-wide pressure while allies cycle skills faster

### Key Interactions:
- Terrain at mound edges becomes death zones for Landslide Step
- Consecrated ground makes MOUND KING mobile threat (move every turn)
- Topiary Breath arranges enemies for maximum Landslide Step damage
- Earthmover (passive) lets LANDSCAPER reposition through her own sculpted battlefield

---

## Design Questions Still to Resolve

1. **Passive final choice** - Which Earthmover variant (or alternative)?
2. **LANDSCAPER base stats** - HP/ATK/DEF/Movement/Range?
3. **Ground Swell emergence time** - 2 or 3 turns before MOUND KING spawns?
4. **Topiary Breath specifics:**
   - Exact cone dimensions?
   - Banishment duration (flat or distance-scaled)?
   - What specific "pattern" are enemies/terrain forced into?
5. **Sculptor's Foundation details:**
   - Zone size (2x2, 3x3, 4x4)?
   - Duration (2-3 turns or indefinite)?
   - Placement range?
6. **MOUND KING combat details:**
   - Exact HP/DEF/PRT values for "unkillable" feel?
   - Attack range (melee only or short range)?
   - Movement range (definitely 1, or possibly 2)?

---

## Tips (Preliminary)

- LANDSCAPER is a setup unit - early game is about positioning Ground Swell and consecrated ground
- Place consecrated ground where the battle *will be* after MOUND KING emerges, not where it currently is
- Ground Swell clusters terrain at mound edges - this creates Landslide Step damage corridors
- MOUND KING has a 3-turn lifespan - make every move count
- Buried Alive punishes enemies camping the mound - they'll be immobilized when he emerges
- Topiary Breath is both battlefield reset and setup - forces enemies into Landslide Step patterns
- Consecrated ground makes skills with 2-turn cooldown usable every turn
- MOUND KING on consecrated ground can move every turn (Landslide Step cooldown 0)
- Don't try to kill MOUND KING - he's nearly unkillable and dies automatically after 3 turns

## Tactical Notes (Preliminary)

- **Strong against:** Static formations, terrain-heavy maps, teams that rely on positioning
- **Weak against:** High mobility units that can avoid Landslide Step zones, units that can kite MOUND KING
- **Positioning:** LANDSCAPER should stay mobile with Earthmover, place Ground Swell in central/chokepoint locations
- **Timing:** MOUND KING's 3-turn window is your power spike - coordinate team around it
