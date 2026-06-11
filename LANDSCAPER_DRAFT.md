# LANDSCAPER — Unit Design Document

## Identity

A four-armed, dragon-masked terrain manipulator wielding quartz crystal tuning forks
in each hand and wearing a Tibetan horn semi-circle array on her helmet. She reshapes
the battlefield through acoustic resonance — grabbing terrain, building walls, shattering
obstacles, and turning units into garden sculptures. Low personal damage output but
devastating when buffed by teammates and given time to sculpt the field.

## Stats

| Stat | Value | Notes |
|------|-------|-------|
| HP | 20 | Mid-range durability |
| ATK | 1 | Lowest in the game (Derelictionist has 0). Four-hit passive compensates. |
| DEF | 1 | Standard melee defense. |
| Move | 3 | Average mobility |
| Range | 1 | Melee — must be in the thick of it to proc Translative Stroke |

**Unique stat line**: (20, 1, 1, 3, 1) — no other unit shares this combination.
Only unit with ATK 1. The low ATK + melee profile is entirely unique.

## Skills

### Passive: Translative Stroke

**Mechanic**: The Landscaper's basic attack hits **4 times** simultaneously (one strike
per tuning fork). Each hit deals damage independently using the standard damage formula:
`max(1, ATK - DEF)`. Her skill cooldowns are reduced by the **total damage dealt** across
all four hits.

**Thematic**: She manipulates the timing of her skills using the resonant frequencies of
her quartz tuning forks — each strike recalibrates the harmonic cycle, accelerating her
next skill.

**Damage examples**:
- ATK 1 vs DEF 0: 4 × 1 = 4 damage, cooldowns reduced by 4
- ATK 1 vs DEF 3: 4 × 1 = 4 damage (minimum 1 per hit), cooldowns reduced by 4
- ATK 3 (buffed) vs DEF 1: 4 × 2 = 8 damage, cooldowns reduced by 8
- ATK 5 (heavily buffed) vs DEF 2: 4 × 3 = 12 damage, cooldowns reduced by 12

**Key interactions**:
- PRT (Partition shield) blocks 1 damage per hit — very effective against her (blocks 4 total)
- Ossify reflect triggers per hit — risky to attack Ossified targets
- ATK buffs from teammates (Site Inspection, Investment maturity)
  dramatically increase both her damage output and cooldown cycling speed
- Each of the 4 hits can independently trigger critical health / retching

**Design intent**: Incentivizes the Landscaper to be in melee range attacking every turn,
and incentivizes teammates to buff her ATK. Her skill cooldowns need to be carefully
balanced around the assumption that she's reducing them by 4+ per turn.

---

### Active 1: Hornswoggle

**Type**: Terrain manipulation — grab, drag, deposit
**Target**: Directional (8 directions)
**Beam Range**: 3 tiles
**Drag Range**: 3 tiles
**Slag Duration**: 3 turns
**Cooldown**: 8

**Mechanic**:
1. The Landscaper chooses one of 8 directions (N, NE, E, SE, S, SW, W, NW)
2. A sonic wave fires from her horn array in that direction, traveling up to 3 tiles
3. The wave stops when it hits a **terrain or furniture tile** — this tile is **grabbed**
   - If the wave hits a unit before terrain, or reaches max range with no terrain: skill fails
   - Can grab dynamic terrain: Marrow Dike walls, Derelict buildings, Rails, slag walls, etc.
   - Can grab permanent terrain: limestone, pillars, stained stone, furniture
4. The grabbed terrain is **removed** from its original position (becomes empty ground)
5. The terrain is **dragged** from the grab point in the **90° counter-clockwise direction**
   relative to the wave direction, traveling up to 3 tiles
6. Along the drag path, each empty tile receives a **slag wall** (temporary blocking terrain)
7. If the drag path hits a blocked tile (terrain, unit, map edge), the terrain stops early
   and is deposited on the last valid empty tile
8. The grabbed terrain is **deposited** at the final position of the drag path

**Drag direction table (90° CCW from fire direction)**:

| Fire Direction | Drag Direction |
|----------------|----------------|
| N              | W              |
| NE             | NW             |
| E              | N              |
| SE             | NE             |
| S              | E              |
| SW             | SE             |
| W              | S              |
| NW             | SW             |

**What gets created**:
- Original terrain position → empty ground
- Drag path tiles → slag walls (temporary, 3-turn duration, blocks movement and LOS)
- End of drag path → the original terrain/furniture, relocated

**Pinwheel pattern**: When all 8 directions are visualized simultaneously, the wave
spokes and drag arms form a counter-clockwise pinwheel. See HORNSWOGGLE_DRAFT.md for
full trajectory diagrams.

**Design intent**: The bread-and-butter skill. Reshapes the battlefield every time it's
used — opening paths, closing them, relocating furniture (denying/granting Delphic
Appraiser value), building temporary walls, and setting up Dissonance targets. The 90°
CCW drag rule is bizarre at first but completely predictable once learned. High skill
ceiling, high reward.

---

### Active 2: Topiary Breath

**Type**: Displacement + crowd control — transforms units into terrain
**Target**: Directional cone (8 directions), self-cast origin
**Range**: 0 (originates from Landscaper's position)
**Cone depth**: 4 tiles
**Duration**: 1 turn (transformed units revert after 1 turn)
**Cooldown**: TBD
**Affects**: ALL units in cone (allies and enemies)

**Mechanic**:
1. The Landscaper chooses one of 8 directions
2. A blast of resonance erupts from her horn array in a cone shape
3. **All units** caught in the cone (allies AND enemies) are:
   - **Rearranged** into a checker/grid pattern within the cone
   - **Transformed into topiary terrain** — ornamental hedge sculptures
4. Topiary-units become **terrain** for 1 turn:
   - They **cannot act** (skip their next action)
   - They **block movement** (other units cannot walk through them)
   - They **block line of sight** (ranged attacks cannot pass through them)
   - They are **valid targets for Hornswoggle** (can be grabbed and dragged like any terrain)
   - They are **valid targets for Dissonance** (can be shattered for 8-directional shrapnel;
     the shattered unit takes ATK×2 piercing damage in addition to the shrapnel hitting others)
5. After 1 turn, surviving topiary-units **revert to normal units** at whatever
   position they currently occupy (which may have changed if Hornswoggled)

**Cone shape** (firing North):
```
. . # # # # # # # . .    ← row 4: 7 tiles wide
. . # # # # # # # . .    ← row 3: 7 tiles wide
. . . # # # # # . . .    ← row 2: 5 tiles wide
. . . . # # # . . . .    ← row 1: 3 tiles wide
. . . . . @ . . . . .    ← Landscaper (origin)
```

**Width per row from caster**:
- Distance 1: 3 tiles wide (1 center + 1 each side)
- Distance 2: 5 tiles wide (1 center + 2 each side)
- Distance 3: 7 tiles wide (1 center + 3 each side)
- Distance 4: 7 tiles wide (plateaus at max width)

**Checker pattern**: Units caught in the cone are rearranged into a grid pattern with
gaps between them — no two topiary-units are adjacent to each other. This guarantees:
- There is always a walkable path between topiaries
- Dissonance shrapnel can travel through the gaps
- The arrangement is predictable once the player understands the pattern

**Example** (firing North, 3 enemies + 1 ally caught):
```
Before:                         After:
. . . . . . . . . . .          . . . . . . . . . . .
. . . . . . . . . . .          . . . T . T . T . . .
. . . E . . E . . . .          . . . . . . . . . . .
. . . . E . A . . . .          . . . . T . . . . . .
. . . . . @ . . . . .          . . . . . @ . . . . .

T = topiary (was unit), E = enemy, A = ally
```

All four units are redistributed into a checker pattern within the cone. Both allies
and enemies are affected — careless aim petrifies your own team.

**Key interactions**:
- **Hornswoggle + Topiary Breath**: Transform an enemy into a topiary, then Hornswoggle
  them across the map. When they revert next turn, they're completely out of position.
  Slag walls are left in their wake. The most powerful displacement combo in the game,
  requiring two skill casts to execute.
- **Dissonance + Topiary Breath**: Transform enemies into topiaries, then Dissonance one.
  The shattered enemy takes ATK×2 piercing damage AND sends shrapnel into nearby units. The
  enemy literally becomes the bomb. Other topiary-units block the shrapnel, creating
  tactical decisions about which topiary to detonate.
- **Self-sabotage risk**: Catching allies in the cone freezes them for 1 turn. Careful
  aiming is essential. The wide cone at max range makes precise targeting difficult in
  crowded fights.
- **Counterplay**: Units immune to effects (Grayman with Stasiality) may resist
  transformation. Positioning outside cone range (stay behind or beside the Landscaper,
  not in front) avoids the skill entirely.

**Thematic**: The Landscaper's horn array blasts a wave of petrifying resonance that
transforms living creatures into topiary sculptures — ornamental garden hedges shaped
like the units they once were. The "breath" is the sound wave itself, carrying the
harmonic frequency that crystallizes organic matter into plant form.

**Design intent**: The Landscaper's tempo and crowd control skill. It freezes a section
of the battlefield for 1 turn, buying time and creating setup opportunities. The checker
pattern displacement means the board state changes dramatically with each cast — units
end up in new positions, creating fresh Hornswoggle and Dissonance opportunities. The
ally-affecting nature demands careful positioning and rewards high game sense. Benefits
from Translative Stroke cycling — each cast catches different units in different positions.

---

### Active 3: Dissonance

**Type**: Terrain destruction — area piercing damage
**Target**: Adjacent terrain/wall tile (range 1)
**Shrapnel range**: 3 tiles per direction
**Damage**: ATK×2 piercing (ignores DEF, only PRT reduces; base ATK 1 = 2 damage)
**Cooldown**: 4

**Mechanic**:
1. The Landscaper targets a terrain, furniture, or wall tile **adjacent to her** (range 1)
2. She strikes the tile with all four tuning forks simultaneously, **shattering it**
3. The tile is **destroyed** (becomes empty ground)
4. Shrapnel flies outward in **all 8 directions** from the shattered tile
5. Each shrapnel line travels up to 3 tiles
6. Shrapnel deals **ATK×2 piercing damage** to every unit it passes through
   - Piercing: ignores DEF entirely, only PRT (Partition) can reduce it
7. Shrapnel **stops at terrain** — walls provide cover from the explosion
8. Shrapnel **passes through units** — multiple units in the same line all take damage

**Shattering topiary-units**: If the Landscaper Dissonances a topiary-unit (created by
Topiary Breath), the transformed unit takes **ATK×2 piercing damage** from the shatter itself,
AND shrapnel radiates outward from their position as normal. The unit becomes the bomb.
If the unit survives, they revert to normal at their current position (now empty ground
where they were shattered). If they die, standard death/GP/respawn rules apply.

**Example**: Landscaper shatters a slag wall. An enemy is 1 tile north of the wall and
another enemy is 2 tiles north. Both take ATK×2 piercing damage. A third enemy is 2 tiles
east but behind a limestone pillar — the shrapnel stops at the pillar, that enemy is safe.

**What can be shattered**:
- Slag walls (created by Hornswoggle)
- Topiary-units (created by Topiary Breath) — unit takes 3 piercing + shrapnel radiates
- Marrow Dike walls
- Derelict building tiles
- Limestone, pillars, stained stone
- Furniture (lecterns, coat racks, ottomans, etc.)
- Rails
- Any terrain that blocks movement

**Key interactions**:
- Hornswoggle creates slag walls → Dissonance detonates them for area damage
- Topiary Breath creates topiary-units → Dissonance shatters them (unit takes damage + shrapnel)
- Destroying permanent terrain permanently changes the map
- Destroying furniture removes Delphic Appraiser astral value positions
- Shrapnel stopping at terrain means enemies can hide behind other walls
  (including other topiary-units — choosing which topiary to shatter matters)
- The Landscaper must be adjacent (range 1) — she's always in the blast zone's
  center ring, but shrapnel fires FROM the tile, not from her, so she's not hit
- PRT (Partition shield) blocks 1 per shrapnel hit

**Thematic**: A dissonance is a musical instrument made of resonant stones — struck to
produce tones. The Landscaper strikes terrain like an instrument, but the resonance is
so violent it shatters the stone entirely, sending fragments everywhere.

**Design intent**: The Landscaper's payoff skill. She spends turns building terrain with
Hornswoggle and creating topiary-units with Topiary Breath, then cashes in with Dissonance
for area piercing damage. Consuming terrain to deal damage creates a constant
build-destroy rhythm. The range 1 requirement means she has to be in the thick of it,
which also feeds Translative Stroke via basic attacks. High setup cost, high reward.

---

## Combo Loops

**The Landscaper's core gameplay loop**:

1. **Hornswoggle** terrain into position near enemies, creating slag walls along the path
2. **Basic attack** in melee to deal 4 hits and cycle cooldowns via Translative Stroke
3. **Dissonance** a slag wall adjacent to clustered enemies for 3 piercing to each
4. Repeat — Hornswoggle builds more terrain, Dissonance spends it

**The Landscaper's advanced combos**:

- **Topiary → Dissonance**: Transform enemies into topiaries, walk up to one, shatter it.
  The shattered enemy takes 3 piercing and shrapnel hits everyone around them. Other
  topiary-units in the shrapnel path block it, creating tactical choices about which
  to detonate.
- **Topiary → Hornswoggle**: Transform an enemy, then Hornswoggle them across the map.
  They revert next turn completely out of position, with slag walls blocking their return.
  The ultimate displacement combo — requires two skills and precise aim.
- **Hornswoggle → Topiary → Dissonance**: Build slag walls to funnel enemies, transform
  them into topiaries in a cluster, then shatter one for massive multi-target damage.
  The full three-skill combo when everything lines up.

**Synergy with teammates**:
- ATK buffers (Site Inspection, Investment maturity) make her cycle faster
- Displacement skills (Derelict push, Estrange) can shove enemies into Dissonance kill zones
- Marrow Condenser builds walls → Landscaper can Hornswoggle or Dissonance them
- Topiary Breath can freeze enemies in place for allies to set up on
- Topiary Breath can also freeze allies — communication/coordination is key in
  local multiplayer

**Counterplay**:
- PRT (Partition) is very effective — blocks 1 per Translative Stroke hit (4 total) and
  reduces Dissonance piercing
- Staying away from terrain denies Dissonance setups
- Staying behind or beside the Landscaper (not in front) avoids Topiary Breath cone
- Her ATK 1 means she's weak alone — focus her when separated from her team
- Destroying her slag walls before she can Dissonance them wastes her setup
- Spreading out reduces Topiary Breath value and Dissonance multi-hits
- Effect immunity (Grayman Stasiality) may resist Topiary Breath transformation

---

## Upgrades (4 total — one per skill)

TBD — to be designed after base kit is finalized and playtested.

Candidates to explore:
- **Translative Stroke upgrade**: each hit applies a small debuff to the target?
  Or 5th hit added? Or cooldown reduction also heals 1 HP per skill cycled?
- **Hornswoggle upgrade**: increased drag range, or slag walls deal damage when walked
  through, or wave passes through units to reach terrain behind them? Or slag walls
  grant LOS removal to allies (the Prima Vista concept, repurposed as an upgrade)?
- **Topiary Breath upgrade**: increased duration (2 turns), or topiary-units explode
  on revert dealing minor damage to adjacent units, or the checker pattern becomes
  denser (units pushed closer together)?
- **Dissonance upgrade**: increased shrapnel range, or shrapnel leaves behind hazard
  tiles, or triggers chain reactions with adjacent slag walls/topiaries?

---

## Cooldowns

Cooldowns need careful balancing around Translative Stroke. With 4 minimum damage per
basic attack, she reduces cooldowns by 4 every turn she attacks. If buffed, she reduces
even faster.

**Final values**:
- Hornswoggle: **5** (fast terrain reshaping)
- Topiary Breath: **13** (powerful CC needs longer cooldown)
- Dissonance: **5** (fast but consumes terrain)

---

## Implementation Checklist

When ready to implement:

### Done (text mode)
- [x] Add LANDSCAPER to UnitType enum in constants.py
- [x] Add stat tuple (20, 1, 1, 3, 1) to UNIT_STATS
- [x] Add display name, symbol, attack effect to constants.py
- [x] Add to GP_ELIGIBLE_UNITS
- [x] Create boneglaive/game/skills/landscaper.py
- [x] Register skills in boneglaive/game/skills/registry.py
- [x] Add upgrades to boneglaive/game/upgrades.py (placeholders)
- [x] Add to recruitment order in boneglaive/game/recruitment.py
- [x] Add to setup_window.py unit list and display names (graphical + text)
- [x] Create terrain types SLAG_WALL and TOPIARY in map.py
- [x] Add to text mode UI (skill menu, help data, unit selection, status effects)
- [x] Handle Translative Stroke 4-hit logic in engine.py
- [x] Handle Hornswoggle wave/grab/drag/slag in engine.py
- [x] Handle Topiary Breath cone/transform/checker/revert in engine.py
- [x] Handle topiary-unit interaction with Hornswoggle and Dissonance
- [x] Handle Dissonance shatter/shrapnel in engine.py
- [x] Handle slag wall and topiary duration processing in engine.py
- [x] Topiary status effect across all systems (999 PRT, immunity, action blocking)
- [x] ASCII animations for all skills and basic attack
- [x] Terrain rendering (slag walls, topiaries) in text mode

### Remaining
- [ ] Create graphics/terrain/slag_wall.svg
- [ ] Create skill icon SVGs (hornswoggle.svg, topiary_breath.svg, dissonance.svg)
- [ ] Add AI handling in tactical_evaluator.py
- [ ] Create boneglaive/graphical/animations/landscaper.py
- [ ] Add to animation_factory.py
- [ ] Add sound entries to sound_registry.py
- [ ] Design and implement upgrades (4 total)

## STATUS: TEXT MODE COMPLETE — graphical mode, AI, upgrades remaining
