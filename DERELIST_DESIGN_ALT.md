# DERELIST - Unit Design Outline

## Core Concept & Thematics
The DERELIST is a pure support/healer unit that operates through psychological abandonment and trauma processing. Rather than traditional healing, he helps allies process battlefield trauma through abreactive responses, gaining power through distance and leaving behind haunted echoes of processed pain.

**Visual Identity**: A detached figure in tattered robes.

## Base Statistics
**HP**: 18 | **Attack**: 2 | **Defense**: 0 | **Move Range**: 3 | **Attack Range**: 1
- Lower HP than most units (fragile support)
- Minimal attack power (not meant for combat)
- No defense (relies on positioning and distance)
- Conditional mobility (average normally, exceptional after using skills)
- Short attack range (emergency only)

## SEVERANCE (Passive Skill)
**Core Mechanic**: Skill-then-move capability
- The DERELIST has the unique ability to issue a move command after he uses a skill
- When moving after using a skill, his movement range is increased to 4 (from base 3)
- **Restriction**: The DERELIST cannot move twice in one turn - if he moves first, then uses a skill, he cannot move again
- Allows for dramatic repositioning to maximize distance-based healing effects
- Creates hit-and-run support gameplay

## Active Skills

### 1. VAGAL RUN (Key: V)
**Range**: 3 | **Cooldown**: 4 turns | **Target**: Single Ally

**Immediate Effect**:
- Ally gains **+3 Attack** bonus
- Applies "Trauma Processing" status (no duration limit)

**Trauma Processing Status**:
- 50% of damage taken is stored as "trauma debt"
- Attack bonus persists until status is removed

**Abreaction Trigger** (when ally takes any damage):
- Ally takes stored trauma damage
- Immediately heals for: stored damage + (1 HP per tile distance from DERELIST)
- **Removes ALL negative status effects** (including Trauma Processing itself)
- Attack bonus ends

**Strategic Design**: Creates dilemma for enemies - allow permanent +3 attack or trigger powerful heal + full cleanse.

### 2. DERELICT (Key: D)
**Range**: 3 | **Cooldown**: 4 turns | **Target**: Single Ally
- **Simplified**: Push ally 4 tiles away in straight line (blocked by terrain/units)
- Upon landing, ally heals for: 3 HP + (1 HP per tile of final distance from DERELIST)
- **"Derelicted" Status**: Movement reduced to 0 for 1 turn (full immobilization)
- Represents psychological "cutting away" and abandonment therapy

### 3. PARTITION (Key: P)
**Range**: 3 | **Cooldown**: 5 turns | **Target**: Single Ally

**Primary Effect**:
- Grants damage-absorbing shield for 3 turns
- Shield strength: 3 + (1 per 2 tiles DERELIST is away when damage is taken)

**Dissociation Trigger**:
- If ally would reach critical health (≤30% max HP) while shielded
- Damage is completely nullified AND reflected back to the attacker
- DERELIST teleports to random valid position 3+ tiles away from ally
- Ally gains "Derelicted" status for 1 turn (movement reduced to 0)

## Tactical Gameplay Patterns

**Early Game**: Stay close for frequent small heals and trauma induction setup
**Mid Game**: Strategic repositioning to maximize distance scaling on key heals
**Late Game**:

**Positioning Tension**: Must balance accessibility vs power - close for frequent support, distant for powerful interventions.

## Balance Considerations
- **Weaknesses**: Fragile, no combat capability, position-dependent effectiveness
- **Strengths**: Unique healing scaling, powerful emergency saves, tactical immobilization effects
- **Counterplay**: Focus fire the DERELIST before he can establish distance, or force him to stay close

## Integration Notes
- Symbol: 'D' (for DERELIST)
- Compatible with existing status effect systems
- Natural regeneration enhancement integrates with existing healing systems
- Dissociation uses untargetable state similar to INTERFERER's Karrier Rave

This unit fills the dedicated healer role while maintaining thematic coherence with the game's dark, psychological undertones.

## Implementation Status: ✅ COMPLETE
**DERELIST is now fully implemented and playable!**

### What Works:
- ✅ Unit stats and visual integration (HP:18, ATK:2, DEF:0, MOVE:3, RANGE:1, Symbol:'D')
- ✅ Setup phase selection and placement (TAB navigation, unit placement)  
- ✅ Skills menu access ([S]kills → [V]/[D]/[P])
- ✅ Ally targeting system (highlights allies within range 3)
- ✅ **Vagal Run**: +3 attack bonus, trauma processing, strategic abreaction dilemma
- ✅ **Derelict**: 4-tile push, distance-based healing, immobilization
- ✅ **Partition**: Distance-scaled shields, damage reflection, emergency teleport
- ✅ **Severance**: Skill-then-move framework (ready for future enhancement)
- ✅ Status effect processing (Trauma Processing, Derelicted, Partition Shield)
- ✅ Complex damage mechanics (storage, reflection, cleansing)

### How to Play:
1. **Setup**: TAB to DERELIST during unit placement phase
2. **Combat**: Select DERELIST → Press [S] for skills → Press [V]/[D]/[P] 
3. **Target**: Click on highlighted ally within 3 tiles
4. **Strategy**: Use distance positioning to maximize healing effectiveness

**Ready for battlefield psychological support! 🏥💀**