# LANDSCAPER - Unit Help Template (DLC)

## Overview
The LANDSCAPER is a tribal-industrial tech-shaman who manipulates the battlefield through arcane
terraforming technology. This frontline disruptor punishes aggressive burst damage strategies by
growing stronger when heavily damaged in a single turn, forcing enemies to chip away cautiously
or face escalating consequences. The LANDSCAPER's true power lies in her ability to summon and
empower the MOUND KING—an undead nephilim warrior whose strength persists and grows across
multiple lifetimes, creating an escalating long-game threat.

**Role:** Frontline Disruptor / Summoner / Terraformer
**Difficulty:** ★★★

---

## Stats (Base - Subject to Change)
- **HP:** 20
- **Attack:** 3-4 (TBD)
- **Defense:** 1-2 (TBD)
- **Movement:** 2
- **Range:** 1-2 (TBD)
- **Symbol:** L

---

## Abilities

### PASSIVE: Threshold Surge
**[Passive - Always Active]**

When the LANDSCAPER takes significant damage in a single turn, she triggers damage thresholds that
provide immediate tactical benefits and permanently empower her summoned MOUND KING bloodline.

**Threshold Tiers:**
- **5+ damage in one turn:** Reduce all skill cooldowns by 1 turn
- **10+ damage in one turn:** Reduce all skill cooldowns by 2 turns + MOUND KING Power +1
- **15+ damage in one turn:** All skills instantly ready + MOUND KING Power +2

**MOUND KING Power Scaling:**
- Power level persists across LANDSCAPER deaths
- Each future MOUND KING is summoned with accumulated power bonuses
- Power translates to: [TBD - Attack? HP? Both?]

**Tactical Notes:**
- Forces enemies to chip slowly (3-4 damage per turn) to avoid triggering thresholds
- Burst damage strategies backfire—dealing 15+ damage gives LANDSCAPER immediate action advantage
- Creates escalating long-game threat through MOUND KING empowerment
- Thresholds reset each turn (not cumulative across multiple turns)

**Type:** Passive
**Special:** Anti-burst defensive mechanic; persistent cross-death scaling

---

### SKILL 1: [Unearth / Burial Rite / Exhumation - TBD]
**[Active] [Key: TBD]**

The LANDSCAPER channels arcane technology to create a massive burial mound on the battlefield,
displacing existing terrain. After one turn, the MOUND KING—an undead nephilim warrior—emerges
from the mound to fight alongside her.

**Effect:**
- Target: Ground tile within range [TBD: 3-4 tiles?]
- Creates BURIAL_MOUND terrain at target location (displaces existing terrain)
- After 1 turn delay: MOUND KING emerges from the mound
- MOUND KING inherits accumulated Power Level from Threshold Surge

**Mound Properties:**
- [TBD] Impassable while MOUND KING is emerging?
- [TBD] Blocks line of sight?
- [TBD] Persists after emergence or disappears?

**Type:** Active
**Range:** [TBD: 3-4]
**Cooldown:** [TBD: 4-5 turns?]
**Target:** Ground tile
**Special:** Summons MOUND KING after 1 turn delay; displaces terrain

---

### SKILL 2: [Terraforming Skill - Name TBD]
**[Active] [Key: TBD]**

The LANDSCAPER manipulates the battlefield through technological-arcane means, moving or
transforming terrain to disrupt enemy positioning and create tactical advantages.

**Possible Mechanics (To Be Determined):**
- **Option A: Tectonic Shift** - Swap positions of two terrain tiles
- **Option B: Landslide** - Push/move terrain in a direction
- **Option C: Reclamation** - Destroy terrain for a buff
- **Option D: Wild Growth** - Create temporary blocking terrain
- **Furniture Manipulation?** - Can it move furniture? (Strong vs DELPHIC APPRAISER)
- **Impassable Terrain?** - Can it affect pillars/walls?

**Type:** Active
**Range:** [TBD]
**Cooldown:** [TBD]
**Target:** [TBD]
**Special:** [TBD - Terrain displacement/manipulation mechanics]

---

### SKILL 3: [Combat/Utility Skill - Name TBD]
**[Active] [Key: TBD]**

[Description pending - third skill slot for combat ability or additional utility]

**Type:** Active
**Range:** [TBD]
**Cooldown:** [TBD]
**Target:** [TBD]
**Special:** [TBD]

---

## MOUND KING (Summoned Unit)

### Overview
The MOUND KING is an undead nephilim warrior—a descendant of ancient giants wrapped in ceremonial
burial garb. This persistent summon grows stronger with each threshold trigger, maintaining power
across multiple summonings even after the LANDSCAPER dies.

### Stats (Base - Before Power Scaling)
- **HP:** 20
- **Attack:** 4
- **Defense:** 1
- **Movement:** 2
- **Range:** 2
- **Type:** Summon (controllable)

### Power Scaling
- Inherits accumulated MOUND_KING_POWER_LEVEL from LANDSCAPER's Threshold Surge
- Each power level grants: [TBD - +1 attack? +2 HP? Both?]
- Power persists across LANDSCAPER deaths and resummons
- [TBD] Power level cap? Or infinite scaling?

### Behavior
- Fully controllable by player (not autonomous)
- [TBD] Can only have one MOUND KING active at a time?
- [TBD] What happens if LANDSCAPER dies while MOUND KING is alive?
- [TBD] Can MOUND KING be resummoned if it dies?

---

## Tactical Tips

### Playing AS LANDSCAPER:
- **Bait burst damage** - Position aggressively to tempt enemies into triggering thresholds
- **Maximize value** - Taking 10+ damage gives cooldown reduction AND MOUND KING power
- **Long game strategy** - Each match makes future MOUND KINGs stronger
- **Terrain control** - Use displacement to disrupt enemy formations and setups
- **Mound placement** - Strategic burial mound placement can block paths or create cover

### Playing AGAINST LANDSCAPER:
- **Chip damage only** - Deal 3-4 damage per turn to avoid threshold triggers
- **Spread damage** - Multiple small attacks across turns, never burst
- **Kill MOUND KING first** - Prevent power scaling by eliminating summons quickly
- **Avoid clustering** - Terrain displacement can separate your units
- **Early aggression** - Pressure before MOUND KING power scales out of control

---

## Synergies & Counters

### Strong With:
- [TBD] Units that benefit from long games?
- [TBD] Units that can protect her while she accumulates thresholds?
- [TBD] Terrain-dependent units that benefit from her manipulation?

### Strong Against:
- **Burst damage teams** - They trigger thresholds and empower MOUND KING
- **DELPHIC APPRAISER** - Terrain/furniture manipulation disrupts appraisals
- **Positional setups** - Terraforming breaks carefully arranged formations

### Vulnerable To:
- **Sustained chip damage** - Slow, steady damage avoids thresholds
- **High-range units** - Can stay safe while chipping from distance
- **[TBD]** - Other counters?

### Best Positioning:
- **Frontline** - Aggressive positioning to bait threshold triggers
- **Chokepoints** - Force enemies to commit to damage to break through
- **Near objectives** - Forces enemy to choose between objectives or avoiding burst damage

---

## Design Notes (Development)

### Questions to Resolve:
1. Exact threshold values (5/10/15 or different?)
2. MOUND KING power scaling formula
3. Terraforming skill specifics (what can be moved/destroyed?)
4. Third skill slot purpose
5. Power level cap (if any)
6. MOUND KING persistence rules
7. Burial mound terrain properties
8. Base stats finalization

### Thematic Elements:
- **Visual:** Tribal-industrial-cybernetic jungle girl aesthetic
- **Tech-Arcane Fusion:** Technology that appears magical
- **Nephilim Lore:** MOUND KING as undead giant warrior
- **Persistent Threat:** Cross-death scaling creates escalating danger

### Balance Considerations:
- Threshold values must be carefully tuned (too low = always triggered, too high = never triggered)
- MOUND KING scaling needs cap or diminishing returns to prevent infinite growth
- Terrain displacement is unprecedented—requires careful balance vs existing strategies
- Furniture manipulation could be very strong vs DELPHIC APPRAISER

---

## Aesthetic Description

The LANDSCAPER is a young woman who blends tribal warrior aesthetics with industrial cybernetics
and jungle motifs. Her appearance suggests a fusion of ancient shamanic tradition with advanced
technology—perhaps holographic plant projections, neon tribal markings, or circuitry that grows
like roots across her skin. She wields terraforming tools that operate through technological means
but produce effects that seem arcane and primal.

The MOUND KING emerges as a towering undead warrior wrapped in ceremonial burial garb, wearing
armor that speaks of ancient giant-kind rituals. Despite being undead, the MOUND KING maintains
dignity—not a shambling corpse but a preserved warrior king answering an ancient pact.

---

**Status:** Work in Progress - DLC Unit
**Branch:** landscaper
**Last Updated:** [Date TBD]
