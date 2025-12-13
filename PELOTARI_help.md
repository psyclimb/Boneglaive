# PELOTARI - Unit Help

## Overview
The PELOTARI is a high-skill ranged specialist inspired by jai alai (Basque pelota), wielding a cesta to launch ricocheting ball projectiles across the battlefield. This unit excels at disrupting enemy strategies by stealing buffs, reflecting attacks, and controlling space through physics-based projectile mechanics. With unique ricochet and phase-through modes, the PELOTARI rewards players who master trajectory planning and angle calculation.

**Role:** Burst Damage / Disabler / Displacer
**Difficulty:** ★★★★★ (5 Glaives - Highest Complexity)

---

## Stats (Base)
- **HP:** 18
- **Attack:** 4
- **Defense:** 1
- **Movement:** 4
- **Range:** 4 (base), 5-6 (with passive buff)
- **Symbol:** P

---

## Abilities

### PASSIVE: [Name TBD]
**[Passive - Always Active]**

The PELOTARI starts each match with a self-buff that enhances his attack range, allowing him to control the battlefield from extreme distances. This buff refreshes periodically and has unique properties that make it immune to enemy theft.

**Effect:**
- Grants +1-2 attack range (4 → 5-6 total range when buffed)
- Refreshes every 2-3 turns
- Can be voluntarily knocked off to create offensive spread shot

**Unique Property - Spread Shot Conversion:**
When the PELOTARI buff is knocked off (by ally or enemy), it transforms into a **cone of ball projectiles** instead of a steal-able buff ball. This makes it inherently immune to buff theft while providing offensive utility.

**Spread Shot Mechanics:**
- Multiple balls fire in a cone pattern from the point of impact
- Each ball follows current toggle mode (ricochet or phase)
- Deals damage to all units in the spread pattern
- Can be used offensively by knocking buff off allied PELOTARI or yourself

**Tactical Notes:**
- Long range makes PELOTARI difficult to reach
- Losing the buff reduces effective range but can deal AOE damage
- Coordinate with allied PELOTARI to create spread shot combos
- Enemy PELOTARI trying to steal your buff will trigger spread shot instead

**Type:** Passive
**Special:** Range enhancement; converts to spread shot attack when removed

---

### SKILL 1: [Buff Theft - Name TBD]
**[Active] [Key: TBD]**

The PELOTARI launches a precision shot that knocks buffs off enemy units, transforming them into steal-able projectiles. Buffs knocked loose follow ball physics and can be intercepted by the PELOTARI or allies to claim the stolen enhancement.

**Effect:**
- Targets enemy unit within range
- Knocks one buff off the target
- Buff becomes a ball projectile that travels with trajectory physics
- Buff ball can be caught by PELOTARI or allies to steal the effect
- If buff ball doesn't connect with a unit, it disappears

**Special Interaction - Enemy PELOTARI:**
When targeting an enemy PELOTARI's self-buff, the buff converts to a spread shot instead of a steal-able buff ball (due to passive immunity). This creates an AOE attack at the enemy PELOTARI's position.

**Ball Physics:**
- Follows current toggle mode (ricochet or phase)
- Ricochet mode: Bounces once off terrain
- Phase mode: Passes through terrain to reach allies

**Type:** Active
**Range:** 4 (base), 5-6 (with buff)
**Cooldown:** [TBD: 3-4 turns?]
**Target:** Enemy unit with active buffs
**Special:** Buff stealing mechanic; creates steal-able projectiles

---

### SKILL 2: Catch & Return
**[Active] [Key: TBD]**

Drawing on defensive jai alai techniques, the PELOTARI readies his cesta to catch incoming attacks and skills, immediately reflecting them back as ball projectiles. This counter-skill creates mind games against opponents who must choose between attacking the PELOTARI or holding back.

**Effect:**
- Activate to set up counter stance for this turn
- When targeted by enemy attack or skill, catches it
- Immediately reflects the attack/skill back as a ball projectile
- Ball carries the original damage/effects
- Ball follows current toggle mode (ricochet or phase)

**Execution:**
- Activates during action phase (sets up stance)
- Triggers during execution phase when hit
- Reflection is immediate and automatic

**Counter Scenarios:**
- Catches basic attacks → Reflects damage back
- Catches targeted skills → Reflects skill effects back
- Ball trajectory follows ricochet/phase rules
- Multiple attacks in one turn: only catches the first

**Tactical Notes:**
- High cooldown means timing is critical
- Creates psychological pressure on enemies
- Can reflect powerful enemy skills back at them
- Wasted if no one targets you that turn
- Does not work against AOE skills that don't specifically target you

**Type:** Active
**Range:** Self
**Cooldown:** 3-4 turns
**Target:** Self (counter stance)
**Special:** Reflects enemy attacks/skills as ball projectiles

---

### SKILL 3: Cannonball
**[Active] [Key: TBD]**

The PELOTARI charges up and launches a massive, devastating ball projectile at extreme velocity. This power shot is his primary damage tool—a tactical nuke that displaces both units and furniture, potentially slamming targets into terrain for bonus damage.

**Effect:**
- Launches gigantic ball projectile at target location
- **Direct Unit Hit:** 8 damage (reduced by defense) + knockback 3-4 tiles
- **Slam Bonus:** +4 damage if knocked unit hits terrain/furniture
- **Furniture Hit:** Furniture is launched 3-4 tiles, deals 4 damage to units in path
- Furniture relocates to landing position (not destroyed)

**Damage Summary:**
- Base impact: 8 damage
- Maximum single target: 8 + 4 = **12 damage** (with slam)
- Flying furniture: 4 damage per unit hit
- All damage reduced by defense

**Displacement Mechanics:**
- Units knocked back along ball's trajectory
- Furniture launched in ball's direction
- Both travel 3-4 tiles before stopping
- Landing position becomes new location (no destruction)

**Toggle Interaction:**
- **Ricochet Mode:**
  - Ball bounces once off terrain/furniture
  - First furniture hit: Launches it + ball continues
  - Can hit second target after bounce (full damage)
  - Enables bank shots and multi-target hits

- **Phase Mode:**
  - Passes through all terrain (ignores furniture)
  - Hits first unit only
  - 8 damage + knockback, no furniture interaction
  - Guaranteed straight-line hit

**Tactical Uses:**
- **Finisher:** High damage to eliminate wounded enemies
- **Terrain Control:** Reposition furniture (Market Futures anchors, cover, etc.)
- **Area Denial:** Launch furniture into enemy formations
- **Combo Setup:** Knock enemies into advantageous positions

**Type:** Active
**Range:** 4 (base), 5-6 (with buff)
**Cooldown:** 6 turns
**Target:** Unit or furniture
**Special:** Heavy damage nuke; displaces units and furniture

---

### TOGGLE: Ricochet / Phase Mode
**[Toggle Action - 4th Menu Item]**

The PELOTARI can toggle between two ball projectile modes that fundamentally change how his abilities interact with terrain. This toggle affects all ball-based skills and creates strategic depth through positioning and angle planning.

**Ricochet Mode (Default):**
- Balls bounce once off terrain/furniture
- Follows physics trajectory (bank shots possible)
- Full damage on all hits
- Enables creative angle plays
- Requires terrain/furniture for bounces

**Phase Mode:**
- Balls ignore all terrain (pass through walls, furniture, etc.)
- Only bounces off map edges
- Slightly reduced effects in some skills
- Guaranteed straight-line trajectory
- No terrain interaction/displacement

**Skill Interactions:**

**Buff Theft:**
- Ricochet: Buff ball can bounce to reach allies
- Phase: Buff ball passes through obstacles to allies

**Catch & Return:**
- Ricochet: Reflected attack bounces off terrain
- Phase: Reflected attack goes straight through

**Cannonball:**
- Ricochet: Bounces once, can hit multiple targets, launches furniture
- Phase: Straight line only, no furniture interaction, reduced complexity

**Spread Shot (from passive):**
- Ricochet: Each ball in cone can bounce once
- Phase: All balls pass through terrain in straight lines

**Type:** Toggle Action (4th menu item)
**Special:** Fundamentally changes projectile behavior

---

## Tactical Tips

### Playing AS PELOTARI:

**Positioning:**
- **Stay at maximum range** - Your range advantage (especially with buff) keeps you safe
- **Use terrain angles** - In ricochet mode, position near walls for bank shot opportunities
- **Corner control** - Corner positions enable multi-angle ricochets

**Buff Management:**
- **Keep buff up** for maximum range dominance
- **Time voluntary knock-offs** for spread shot AOE when multiple enemies cluster
- **Coordinate with allied PELOTARI** for spread shot combos

**Skill Usage:**
- **Catch & Return timing** - Use when you predict enemy will focus you
- **Cannonball for finishers** - 6-turn cooldown means save it for high-value targets
- **Steal key buffs** - Prioritize stealing defensive buffs (Ossify) or damage buffs

**Toggle Strategy:**
- **Ricochet for creativity** - Bank shots around corners, hit hidden targets
- **Phase for reliability** - Guaranteed hits through terrain when you need consistency
- **Toggle mid-combat** - Adapt to changing battlefield terrain

### Playing AGAINST PELOTARI:

**Counter-Strategies:**
- **Rush early** - Close distance before he establishes range control
- **High-mobility units** - Units like MANDIBLE FOREMAN (Expedite) can close gaps
- **Baiting Catch & Return** - Force him to use it early, then attack during cooldown
- **Avoid buffing heavily** - Don't stack buffs that can be stolen
- **Spread out** - Prevent spread shot from hitting multiple units
- **Block ricochet angles** - Position to limit his bank shot opportunities

**Dangerous Scenarios:**
- Don't cluster when enemy PELOTARI has buff ready to knock off
- Don't focus him when Catch & Return is likely available
- Don't let him reposition furniture to his advantage with Cannonball
- Watch for Cannonball slams near walls (12 damage potential)

---

## Synergies & Counters

### Strong With:
- **Second PELOTARI** - Spread shot combos by knocking each other's buffs off
- **DELPHIC APPRAISER** - Can reposition Market Futures anchors with Cannonball
- **FOWL CONTRIVANCE** - Both control long range, create crossfire
- **Buff-heavy teams** - More buffs to steal means more utility
- **Long-game strategies** - Range advantage grows stronger over time

### Strong Against:
- **Buff-dependent units** - DELPHIC APPRAISER (Valuation Oracle), POTPOURRIST (Bergamot Diffusion)
- **Immobile units** - GRAYMAN can't dodge ricochets, FOWL CONTRIVANCE on rails
- **Skill-reliant units** - Catch & Return punishes INTERFERER, MARROW CONDENSER
- **Clustered formations** - Spread shot and Cannonball punish grouping

### Vulnerable To:
- **High-mobility rushers** - MANDIBLE FOREMAN (Expedite), GLAIVEMAN (Vault)
- **Long-range snipers** - GRAYMAN (outranges him), FOWL CONTRIVANCE (Gaussian Dusk)
- **Immune units** - GRAYMAN (Stasiality) can't have buffs stolen or be affected by status
- **Terrain-blocking strategies** - MARROW CONDENSER walls limit ricochet angles

### Best Positioning:
- **Back line** - Maximum range, protected by teammates
- **Corner positions** - Ricochet opportunities with walls at 90-degree angles
- **Near furniture clusters** - Cannonball becomes more dangerous with furniture to launch
- **Map edges** - Phase mode balls bounce off edges for extended range

---

## Design Philosophy

### Complexity Justification (5 Glaives):

**Why highest complexity?**
1. **Physics calculations** - Ricochet angles require geometry understanding
2. **Toggle management** - Constant decision-making between modes
3. **Timing precision** - Catch & Return requires prediction and reads
4. **Buff tracking** - Must monitor enemy buffs and prioritize targets
5. **Positioning mastery** - Range + angles + furniture = high skill ceiling

### Mechanical Depth:
- **Basic level:** Use long range to stay safe, spam basic attacks
- **Intermediate:** Toggle between modes appropriately, steal important buffs
- **Advanced:** Bank shots around corners, Catch & Return mind games
- **Master:** Cannonball furniture repositioning, spread shot combos with allies

### Skill Expression:
- Angle calculation for ricochet shots
- Predicting enemy actions for Catch & Return
- Furniture manipulation with Cannonball
- Buff priority target selection
- Toggle timing and mode switching

---

## Thematic Elements

### Jai Alai Inspiration:
The PELOTARI is directly inspired by **jai alai** (Basque pelota), one of the fastest ball sports in the world. Players use a curved wicker basket called a **cesta** strapped to their hand to catch and hurl a hard ball (pelota) at speeds exceeding 150 mph against walls in a three-walled court.

**Core Concepts Translated:**
- **Cesta** → Weapon for catching and throwing
- **Ricochet play** → Balls bouncing off court walls
- **Catch & return** → Defensive catches and immediate volleys
- **Speed and power** → Cannonball's devastating impact
- **Angle mastery** → Ricochet mode's bank shot mechanics
- **Court control** → Positioning and zone dominance

### Aesthetic Description:
The PELOTARI is an athletic specialist clad in traditional-meets-tactical gear. He wears a modified **cesta** (wicker throwing basket) integrated with advanced technology—perhaps energy-channeling circuits or reinforced composite materials. His appearance blends the elegance of a professional pelotari with the intensity of a battlefield combatant.

Visual elements might include:
- Curved wicker cesta with glowing energy lines
- Athletic build optimized for throwing power
- Lightweight armor allowing maximum mobility
- Ball projectiles that leave luminous trails
- Dynamic throwing poses showing torque and power
- Basque-inspired color schemes and patterns

The PELOTARI embodies **precision, speed, and control**—a master of trajectory who turns the battlefield into his court.

---

## Development Notes

### Questions to Resolve:
1. Skill names (currently TBD placeholders)
2. Exact buff refresh timing (2 or 3 turns?)
3. Spread shot cone angle and ball count
4. Buff theft skill cooldown (3 or 4 turns?)
5. Catch & Return cooldown (3 or 4 turns?)
6. Range bonus from passive (+1 or +2?)
7. Flying furniture collision interaction details

### Balance Considerations:
- 5-glaive complexity must feel earned (not frustrating)
- Range advantage balanced by low HP (18) and defense (1)
- Cannonball cooldown (6 turns) prevents spam
- Catch & Return cooldown prevents defensive turtling
- Ricochet mode requires skill but rewards creativity
- Phase mode provides accessible alternative for new players

### Implementation Priority:
1. Basic ball projectile physics system (ricochet/phase)
2. Passive buff and spread shot conversion
3. Toggle mechanic (4th action menu item)
4. Buff theft skill with ball physics
5. Catch & Return counter mechanics
6. Cannonball with displacement system
7. Furniture relocation system
8. Visual animations and effects

---

**Status:** Design Complete - Ready for Implementation
**Branch:** pelotari
**Last Updated:** 2025-12-13
