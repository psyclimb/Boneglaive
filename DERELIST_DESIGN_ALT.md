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
**Range**: 3 | **Cooldown**: 3 turns | **Target**: Single Ally
- Applies "Trauma Processing" status effect to target ally
- **While Active**: 50% of damage taken is stored as "trauma debt"
- **At End of Combat Phase**: 
  - Ally takes stored trauma damage (abreaction)
  - Gains attack bonus until end of next turn (based on abreaction damage taken)
  - Receives healing: 50% of abreaction damage × distance modifier when the effect falls off
- Status lasts until triggered (no turn limit)

### 2. DERELICT (Key: D)
**Range**: 3 | **Cooldown**: 4 turns | **Target**: Single Ally
- DERELIST "conveys" the ally away from him in a straight line
- Ally is displaced 2-3 tiles away from DERELIST (blocked by terrain/units)
- **Collision Damage**: If ally collides with enemy during displacement:
  - Point blank (0 tiles traveled): 4 damage
  - 1 tile traveled: 3 damage  
  - 2 tiles traveled: 2 damage
  - 3+ tiles traveled: 1 damage (minimum)
- Upon landing, ally is immediately healed based on their new distance from DERELIST
- Healing: 4 HP + (1 HP per tile of final distance, max +6)
- **"Derelicted" Status**: Only applied if final distance ≥3 tiles from DERELIST
  - Effect: Movement reduced to 0 for 1 turn (complete immobilization)
  - Unit can still attack, use skills, and be targeted normally
- Represents psychological "cutting away" and abandonment therapy

### 3. PARTITION (Key: P)
**Range**: 3 | **Dual Cooldown System**:
- **Normal Use**: 3 turns (shield only)
- **Dissociation Triggered**: 7 turns (extended penalty)
- **Target**: Single Ally

**Primary Effect**: 
- Grants damage-absorbing shield
- Shield strength: 2 + (1 per 4 tiles DERELIST is away when damage is taken)
- Shield lasts 3 turns

**Dissociation Trigger**:
- If ally would reach critical health (≤30% max HP) while shielded
- Instead of taking damage: 
  - Damage is negated entirely
  - DERELIST is teleported to the furthest valid position from the affected ally
  - Ally gains "Derelicted" status for 1 turn (movement reduced to 0)
- Skill enters extended 7-turn cooldown

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
- Attack Effect: '~' (psychic disturbance)
- Compatible with existing status effect systems
- Natural regeneration enhancement integrates with existing healing systems
- Dissociation uses untargetable state similar to INTERFERER's Carrier Rave

This unit fills the dedicated healer role while maintaining thematic coherence with the game's dark, psychological undertones.