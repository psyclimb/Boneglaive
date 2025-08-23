# CHIMELORD Unit Design

## Unit Overview
The CHIMELORD is a grotesque, persistent tank whose primary strength is **existing for a long time**. A hollowed out cadaver filled with funerary potpourri - eyeless, with eye sockets stuffed with melange and chest cavity brimmed with perfumed cloves. When it dies, the hollow chest cavity becomes a pit in the ground called the CHIME OAV - filled with chimes and potpourri. Like a breeze through wind chimes, the MELANGE SHADE eventually "chimes in" and wafts forth from the CHIME OAV. Its power lies in persistence through this unique chime-driven resurrection system.

## Core Mechanics
- **Primary Power: Persistence** - The majority of tactical value comes from simply existing across multiple lives
- **Multi-Stage Resurrection**: Three distinct life forms with diminishing returns
- **Universal Maligned Application** - ALL damage dealt by CHIMELORD applies Maligned status effect
- **Secondary: Perfume Ring** - 3x3 area denial effect (moves with unit)  
- **Secondary: Damage Reduction** - 50% penalty for incorrect positioning (applied before armor)

## Maligned Status Effect
- **Duration**: 3 turns (resets on new application, does not stack)
- **Effects**: 
  - Takes 1 damage per turn
  - Attack range reduced by 1 (devastating for ranged units)
- **Applied by**: Any damage dealt by CHIMELORD, CHIME OAV, or MELANGE SHADE
- **Tactical Impact**: Forces ranged units to close distance, disrupts positioning, creates persistent pressure

## Life Stage 1: CHIMELORD

### Stats
- **Health**: Medium-high HP
- **Armor**: Low-medium armor
- **Range**: Ranged attacks
- **Movement**: Standard movement

### Passive Ability: Mélange Eminence
- Creates a 3x3 perfume ring centered on CHIMELORD
- Ring moves when CHIMELORD moves
- Enemies standing OFF the ring deal 50% reduced damage to CHIMELORD
- Damage reduction calculated before armor
- Ring does not interact with terrain/walls
- **Resurrection Power**: Enables transformation into CHIME OAV upon death

### Active Abilities (4)
1. **Resonant Chime** (Key: 'Q', Cooldown: 3, Range: 4) - 4 damage piercing line attack + applies Maligned
2. **Aromatic Drift** (Key: 'W', Cooldown: 4, Range: 0) - Shifts perfume ring 2 tiles for 2 turns; ring damages enemies ending turns on it + applies Maligned  
3. **Melange Cloud** (Key: 'E', Cooldown: 3, Range: 3) - Creates 3x3 cloud for 2 turns; applies Maligned to enemies in area each turn
4. **Implode** (Key: 'I') - Instantly kills the CHIMELORD, triggering transformation to CHIME OAV

## Life Stage 2: CHIME OAV

### Stats
- **Health**: Medium HP (central unit)
- **Armor**: None (stationary)
- **Movement**: Immobile (stationary pit)
- **Duration**: Indefinite - must be destroyed or Imploded to transform
- **Structure**: 1 central unit + 3 subsidiary chimes positioned around it

### Passive Ability: Mélange Eminence (Diminished)
- Creates a 3x3 perfume ring centered on CHIME OAV
- Enemies OFF ring deal 25% reduced damage to CHIME OAV
- Ring remains static (doesn't move)
- **Resurrection Power**: Enables transformation into MELANGE SHADE upon death

### Central Unit (CHIME OAV Core)
- **Active Ability**: **Implode** (Key: 'I') - Instantly kills the central unit and all chimes, triggering transformation to MELANGE SHADE
- **Carries**: Mélange Eminence passive and perfume ring effect
- **Target Priority**: Destroying the central unit kills the entire CHIME OAV structure

### Subsidiary Chimes  
- **Count**: 3 individual chime units positioned around the central unit
- **Stats**: Low HP (2-3 each), stationary, no armor
- **Ability**: "Chime In" - Applies Maligned status to target enemy (Range: 3)
- **Independent Actions**: Each chime can target different enemies each turn
- **Destruction**: Can be killed individually, but all disappear when central unit dies

### Special Properties
- **Multi-Unit Structure**: Central core + 3 subsidiary chimes can be targeted separately
- **Core Destruction**: Killing the central unit eliminates the entire CHIME OAV structure
- **Guaranteed Resurrection**: Always spawns MELANGE SHADE when central unit dies (via combat or Implode)
- **Persistent State**: Remains indefinitely until central unit is eliminated or Imploded
- **Multi-Target Threat**: Can apply Maligned to up to 3 different enemies per turn via individual chimes

## Life Stage 3: MELANGE SHADE

### Stats
- **Health**: Low HP
- **Armor**: Low armor
- **Range**: Reduced range from original CHIMELORD
- **Movement**: Standard movement

### Passive Ability: Mélange Eminence (Inverted)
- Creates a 3x3 perfume ring centered on MELANGE SHADE
- **INVERTED EFFECT**: Enemies standing ON the ring deal 25% reduced damage
- Forces completely different positioning tactics
- Ring moves with MELANGE SHADE
- **Final Form**: No resurrection power - this is the final life stage

### Active Ability (1)
- **Implode** (Key: 'I') - Instantly kills the MELANGE SHADE (final death, no resurrection)

## Tactical Role
- **Primary: Persistence Tank** - Main strength is simply existing for extended periods through multiple lives
- **Map Control Through Presence** - Forces enemies to continually deal with the CHIMELORD threat
- **Resource Drain** - Opponents must invest significant actions/turns to fully eliminate
- **Late-game Insurance** - Provides sustained map presence when other units are eliminated
- **Positioning Disruption** - Secondary benefit from perfume ring mechanics, not primary focus

## Strategic Considerations
- **Power Budget in Longevity**: Damage and utility abilities are deliberately modest - the threat is persistence itself
- **Resource Investment Challenge**: Enemies face difficult decisions about committing actions to fully eliminate vs other priorities  
- **Three-Stage Attrition**: Each life stage forces opponents to continue investing in elimination
- **Time Advantage**: The longer the game goes, the more value CHIMELORD provides through sheer presence
- **Positioning is Secondary**: Ring mechanics provide tactical flavor but core power is resurrection cycle

## Implementation Notes
- Three separate unit types that transform into each other
- Each stage needs unique skill implementations
- Perfume ring system needs area-of-effect tracking
- Resurrection mechanics need turn-based timing system