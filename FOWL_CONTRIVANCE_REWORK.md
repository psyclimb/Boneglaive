# FOWL CONTRIVANCE - Mechanical Rail Artillery Platform Rework

## Concept
The FOWL CONTRIVANCE is a mechanical peacock built into a tall skid that moves along a rail network. It operates as an "on-rails shooter" with devastating long-range artillery capabilities, featuring both a rail gun and mortar systems. The unit generates its own rail infrastructure and becomes a map control specialist.

## Base Stats
- **HP**: 18 (reduced from current - glass cannon artillery)
- **Attack**: 5 (rail gun attack power)
- **Defense**: 0 (very light armor - relies on positioning)
- **Move Range**: 4 (fast on rails)
- **Attack Range**: 2 (standard mortar range when not using rail gun)

## Movement Rules
- Can only move along **Rail Network** tiles (generated when first FOWL CONTRIVANCE spawns)
- If no valid rail path exists to target location, cannot move there
- Can move through other units on rails (shares track)
- **Rail exclusivity**: Only FOWL CONTRIVANCE units can use rails for movement

---

## PASSIVE SKILL: Rail Genesis

**Description**: "The first FOWL CONTRIVANCE to deploy establishes a permanent rail network accessible only to mechanical rail units."

### Mechanics:
- **Dynamic Spawning**: When the **first FOWL CONTRIVANCE** (from either player) enters the map, creates a **Rail Network** covering significant map area
  - Rails extend in cross pattern from map center: 8 tiles North, South, East, West
  - Rails also create diagonal branches at 4-tile intervals
  - **Shared infrastructure** - both players' FOWL CONTRIVANCE units can use the same rails
  
- **FOWL-Exclusive Access**: Only FOWL CONTRIVANCE units can interact with rails
  - Other units pass through rails as if they're normal terrain
  - Rails don't block movement, line of sight, or abilities for non-FOWL units
  - Rails are completely non-interactive for all other units and abilities
  
- **Rail Sharing**: Multiple FOWL CONTRIVANCE units can occupy same rail tile.  FOWL CONTRIVANCE gets placed on a rail
  closest to where the player placed them during the setup phase.
- **Permanent Infrastructure**: Rails persist for entire match once created and cannot be damaged or destroyed

- **Death Explosion**: When FOWL CONTRIVANCE dies:
  - Deals **4 damage** to any enemy units standing on rail tiles
  - **Rails remain intact** and continue to function unless there are no FOWL CONTRIVANCEs left.
  - Allies on rails take no damage (friendly fire protection).

---

## ACTIVE SKILL 1: Gaussian Dusk

**Cooldown**: 4 turns | **Range**: Entire map | **Target**: Direction

**Description**: "Charges a devastating rail gun shot that pierces everything in its path. Must charge for 1 turn before firing."

### Two-Phase Mechanics:

**Phase 1 - Charging Turn**:
- Select firing direction (8 cardinal/diagonal directions)
- Unit cannot move or use other skills this turn
- Charging indicator appears showing planned shot path
- Can be interrupted if unit takes damage or is forced to move

**Phase 2 - Firing Turn** (next turn, if no other action taken):
- Fires automatically at start of turn before any other actions
- **Pierce Effect**: Shot travels entire map length in chosen direction
- **Terrain Destruction**: Destroys destructible terrain in path
- **Enemy Piercing**: Hits ALL enemies in straight line path
- **Defense Bypass**: Completely ignores enemy defense
- **Damage**: 12 damage per enemy hit.
- **Line of Sight**: Ignores LOS requirements completely

### Tactical Notes:
- Incredible range and power but requires setup
- Vulnerable during charging phase
- Can hit multiple enemies if they line up
- Destroys cover for future engagements

---

## ACTIVE SKILL 2: Big Arc

**Cooldown**: 4 turns | **Range**: 6 tiles | **Target**: Area (3x3)

**Description**: "Launches explosive mortar shells in a 3x3 area. Indirect fire ignores line of sight."

### Mechanics:
- **Indirect Fire**: Ignores line of sight requirements
- **Area Effect**: Hits all units in 3x3 target area
- **Damage**: 8 damage to primary target, 5 damage to adjacent targets.
- **Terrain Interaction**: Can target areas behind walls/cover
- **Self-Damage Protection**: Cannot target own tile or adjacent tiles


---

## ACTIVE SKILL 3: Fragcrest

**Cooldown**: 3 turns | **Range**: 4 tiles | **Target**: Single enemy

**Description**: "Deploys a directional fragmentation burst that fans out in a cone, firing explosive shrapnel that blasts enemies backward and embeds fragments for ongoing damage."

### Mechanics:
- **Cone Attack**: Fires in a 90-degree cone emanating from FOWL CONTRIVANCE toward target
- **Multi-Hit Spread**: Primary target takes 4 damage, all other enemies in cone take 2 damage
- **Knockback Force**: All enemies hit are pushed 2 tiles directly away from FOWL CONTRIVANCE
- **Shrapnel Effect**: All enemies hit suffer "shrapnel" - take 1 damage at start of each of their next 3 turns from embedded fragments
- **Cone Range**: Cone extends 4 tiles from FOWL CONTRIVANCE in target direction
- **Line of Sight**: Requires clear line of sight to primary target
- **Normal Defense**: Damage is reduced by enemy defense as normal
- **Spread Pattern**: Cone gets wider with distance (1 tile wide at range 1, 3 tiles wide at range 4)

### Tactical Uses:
- Punish grouped enemies with damage, displacement, and ongoing damage
- Push enemies away from critical positions while applying pressure
- Apply sustained damage over time to multiple targets
- Force enemies into hazardous terrain while they're bleeding
- Break up enemy formations with immediate and lasting effects

---

## Design Philosophy

### Strengths:
- Extreme long-range artillery capability  
- Exclusive access to rail network for superior mobility
- High mobility on rails with movement bonus
- Indirect fire capabilities
- Death explosion punishes enemies on rails
- Shared rail infrastructure when multiple FOWL units present

### Weaknesses:
- Very fragile (low HP/defense)
- Movement completely restricted to rail network
- Rail gun requires vulnerable charging phase
- Friendly fire from mortars
- Limited close-range options
- Dependent on rail network spawning

### Tactical Role:
- Long-range artillery support
- Area denial through rail placement
- Map control specialist
- Glass cannon requiring positioning

---

## Implementation Notes

This rework transforms FOWL CONTRIVANCE from its current form into a unique "on-rails shooter" unit that rewards strategic positioning and long-term planning. The rail network creates a permanent, FOWL-exclusive transportation layer that doesn't interfere with other units' gameplay.

### Key Design Elements:

**Dynamic Map Changes**: Rails only appear when FOWL CONTRIVANCE units are present, creating conditional map features that change the tactical landscape.

**Shared Infrastructure**: When multiple players have FOWL CONTRIVANCE units, they share the same rail network, creating interesting positional contests for optimal rail positions.

**Non-Interference Design**: Rails are completely invisible to non-FOWL units, ensuring clean gameplay interactions and avoiding complex collision/blocking scenarios.

**Glass Cannon Artillery**: The unit becomes a fragile but devastating long-range threat that must use its exclusive rail mobility to survive while delivering powerful artillery strikes.

The death explosion mechanic creates a final tactical consideration - enemies must be aware of rail positions even if they can't interact with them, as standing on rails when a FOWL CONTRIVANCE dies can be lethal.

---

## Animation Descriptions

### GAUSSIAN DUSK (Rail Cannon)

**Charging Phase:**
- Peacock crest unfolds upward (ASCII art expands)
- Steam effects with `~` symbols along platform
- Cannon barrel extends with `=====` growing longer
- Blue electric crackling with `*` and `+` symbols around barrel
- Red targeting line `---` traces across entire map
- Peacock eye-feathers pulse with alternating colors

**Firing Phase:**
- Screen flash (brief white screen or bright color)
- Blue beam `████` shoots across map leaving trail
- Platform recoils backward on rails
- Terrain explosions `*BOOM*` sequence along beam path
- Enemy units flash blue before damage numbers appear
- Cannon retracts, small `*` sparks around peacock

### BIG ARC (Mortar Barrage)

**Launch:**
- Back section opens revealing `|||` mortar tubes
- Tail feathers spread wide in display pattern
- Shells launch `o` `O` `●` ascending with smoke trails `~`
- Projectiles arc overhead across screen

**Impact:**
- Shells `●` descend on target area
- Explosions `*BOOM*` in sequence across 3x3 grid
- Smoke clouds `▓▒░` billow from impact points
- Debris `·` `°` scatters outward

### FRAGCREST (Cone Shrapnel)

**Deployment:**
- Peacock tail fans out in full ASCII display
- Eye-feathers glow with pulsing `●` symbols
- Small cannon ports `°` appear along tail

**Firing:**
- Simultaneous muzzle flashes `*` across fanned tail
- Cone of fragments `·` `°` `•` spreads outward
- Hit enemies flash orange and get pushed back
- Metal fragments `·` embed in terrain with `ping!` text

**Aftermath:**
- Tail folds back to resting position
- Smoke wisps `~` from closed cannons
- Shrapnel in enemies glints with periodic `·` highlights

Each animation uses simple ASCII symbols but creates dramatic visual sequences appropriate for the text-based environment.