# BONEGLAIVE - UNIT REFERENCE GUIDE

## Base Unit Stats
| Unit | HP | Attack | Defense | Move Range | Attack Range |
|------|---|--------|---------|------------|--------------|
| GLAIVEMAN | 22 | 5 | 1 | 2 | 2 |
| MANDIBLE FOREMAN | 22 | 3 | 1 | 2 | 1 |
| GRAYMAN | 18 | 3 | 0 | 2 | 5 |
| MARROW CONDENSER | 24 | 4 | 2 | 3 | 1 |
| FOWL CONTRIVANCE | 18 | 4 | 0 | 3 | 3 |
| GAS MACHINIST | 18 | 4 | 1 | 3 | 1 |
| DELPHIC APPRAISER | 20 | 4 | 1 | 3 | 2 |
| HEINOUS VAPOR | 10 | 0 | 0 | 3 | 1 |

## GLAIVEMAN
**Passive: Autoclave**
- When at critical health (≤30% HP), releases cross-shaped attack (range 3 in 4 directions)
- Damage: Normal attack minus target defense (min 1)
- Heals for half damage dealt
- One-time use per game

**Active Skills:**
1. **Pry** (Range 1, Cooldown 3)
   - Primary damage: 7 (reduced by defense)
   - Splash damage: 3 to adjacent enemies (reduced by defense)
   - Reduces target's movement by 1 for one turn

2. **Vault** (Range 3, Cooldown 4)
   - Leap over obstacles to any empty position within range

3. **Judgement** (Range 4, Cooldown 2)
   - Damage: 4 (ignores defense)
   - Double damage (8) against targets at critical health

## MANDIBLE FOREMAN
**Passive: Viseroy**
- When attacking, traps enemies in mechanical jaws
- Trapped units cannot move and take damage each turn

**Active Skills:**
1. **Expedite** (Range 4, Cooldown 3)
   - Rush up to 4 tiles in a straight line
   - Damage: 6 (reduced by defense) to first enemy encountered
   - Automatically trap first enemy encountered

2. **Site Inspection** (Range 3, Area 3×3, Cooldown 3)
   - Survey a 3×3 area
   - Grants +1 attack and movement to allies for 3 turns if no impassable terrain

3. **Jawline** (Self-targeted, Area 3×3, Cooldown 3)
   - Damage: 4 (reduced by defense) to enemies in 3×3 area around self
   - Completely immobilizes enemies for 2 turns

## GRAYMAN
**Passive: Stasiality**
- Immune to all status effects, displacement, and terrain effects
- Cannot have stats changed positively or negatively

**Active Skills:**
1. **Delta Config** (Range 99, Cooldown 12)
   - Teleport to any unoccupied tile on the map

2. **Estrange** (Range 5, Cooldown 3)
   - Damage: 3 (ignores defense)
   - Applies permanent -1 penalty to all target's stats

3. **Græ Exchange** (Range 3, Cooldown 4)
   - Create an echo (5 HP, 3 attack) at current position and teleport away
   - Echo can attack but not move and lasts 2 turns

## MARROW CONDENSER
**Passive: Dominion**
- When a unit dies inside Marrow Dike, gains permanent upgrades:
  - First death: +1 defense
  - Second death: +1 attack
  - Third death: +1 movement
  - Deaths also upgrade active skills

**Active Skills:**
1. **Ossify** (Self-targeted, Cooldown 3)
   - Gain +2 defense (+3 when upgraded) at cost of -1 movement for 2 turns

2. **Marrow Dike** (Self-targeted, Area 5×5, Cooldown 2)
   - Creates bone walls that block movement for 4 turns
   - Upgraded: Enemies inside take -1 movement penalty, walls have more HP

3. **Bone Tithe** (Self-targeted, Area 3×3, Cooldown 2)
   - Damage: 1 per enemy hit (scales with kill count when upgraded)
   - Gain +1 HP per enemy hit (+2 HP when upgraded)

## FOWL CONTRIVANCE
**Passive: Wretched Decension**
- When an enemy is reduced to critical health, chance to instantly kill:
  - 100% chance with 1 FOWL CONTRIVANCE
  - 50% chance with 2
  - 25% chance with 3+

**Active Skills:**
1. **Murmuration Dusk** (Range 3, Area 3×3, Cooldown 3)
   - Damage: 6 (reduced by defense) to enemies in 3×3 area

2. **Flap** (Range 4, Cooldown 2)
   - Damage: 9 (reduced by defense) to single target

3. **Emetic Flange** (Self-targeted, Area 3×3, Cooldown 3)
   - Damage: 4 (reduced by defense) to surrounding enemies
   - Pushes enemies back 1 tile

## GAS MACHINIST
**Passive: Effluvium Lathe**
- Generates 1 Effluvium charge per turn (max 4)
- Charges extend HEINOUS VAPOR duration (1 charge = 1 turn)

**Active Skills:**
1. **Broaching Gas** (Range 3, Cooldown 2)
   - Summons HEINOUS VAPOR (Φ) that deals 2 damage to enemies
   - Cleanses allies of negative status effects
   - Duration: 1 turn + 1 per Effluvium charge

2. **Saft-E-Gas** (Range 3, Cooldown 3)
   - Summons HEINOUS VAPOR (Θ) that blocks enemy ranged attacks
   - Heals allies by 1 HP per turn
   - Duration: 1 turn + 1 per Effluvium charge

3. **Diverge** (Range 5, Cooldown 4)
   - Splits an existing HEINOUS VAPOR or self into two specialized vapors:
     - Coolant Gas (Σ): Heals allies for 3 HP
     - Cutting Gas (%): Deals 3 pierce damage to enemies

## DELPHIC APPRAISER
**Passive: Valuation Oracle**
- Perceives the "cosmic value" (1-9) of furniture
- When adjacent to furniture: +1 defense and attack range

**Active Skills:**
1. **Market Futures** (Range 4, Cooldown 6)
   - Creates teleportation anchor for allies
   - Grants +1 ATK (turn 1), +2 ATK (turn 2), +3 ATK (turn 3)
   - Also grants +1 range for all 3 turns

2. **Auction Curse** (Range 3, Cooldown 2)
   - Applies DOT effect (1 damage per turn)
   - Duration equals average furniture value
   - Gives 1 bid token per furniture to ally (heals 2 HP per token)

3. **Divine Depreciation** (Range 3, Area 5×5, Cooldown 4)
   - Deals damage bypassing defense
   - Pulls enemies toward center based on their movement
   - Rerolls cosmic values of all other furniture