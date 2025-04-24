# FOWL CONTRIVANCE - Revised Unit Concept

## Overview
A high-damage nuker unit composed of synchronized bird flocks forming a hooked cross in the sky. FOWL CONTRIVANCE exists solely to obliterate enemy units with overwhelming avian fury, sacrificing all utility and survivability for pure, devastating damage output.

## Visual Representation
- **Symbol:** `^` (representing birds in flight)
- **Colors:** Deep blues, blacks, with flashes of bright red
- **Animations:** Swirling, diving, and exploding bird patterns

## Base Stats
- **HP:** 14 (lowest of all units)
- **Attack:** 7 (highest base attack)
- **Defense:** 0 (extremely vulnerable)
- **Move Range:** 3 (average)
- **Attack Range:** 3 (good range)

## Passive Ability: Wretched Decension (with Flock Loyalty Mechanic)
When FOWL CONTRIVANCE causes a unit to retch (reduced to critical health), that unit may instantly perish instead, with the flock descending to carry away the near-dead.

**Flock Loyalty Mechanic:**
The effectiveness depends on how many FOWL CONTRIVANCE units are on the same team:
- **Single FOWL CONTRIVANCE:** 100% chance to instantly kill units who retch!
- **Two FOWL CONTRIVANCE units:** 50% chance for each unit's passive to trigger
- **Three FOWL CONTRIVANCE units:** 25% chance for each unit's passive to trigger

**Messages:**
- Success (single unit): "The flocks descends to claim the wretched!"
- Failure: "The flocks fail to coordinate their descent."

**Visual Effect:** Swarm of bird symbols (`^`, `v`, `*`) converges on the target (more dense with fewer FOWL CONTRIVANCE units)

## Active Abilities

### 1. Murmuration Dusk
Medium-range area attack where bird flocks dive-bomb enemy units in intricate patterns.

- **Range:** 3
- **Area:** 3x3
- **Damage:** 8
- **Cooldown:** 3 turns
- **Animation:** Swirling birds (`^`, `v`, `~`, `*`)
- **Targeting:** Centered on target tile
- **Special:** Only affects enemy units, allies remain unharmed

### 2. Flap
Focused single-target attack with extreme damage from a concentrated hawk formation.

- **Range:** 4
- **Damage:** 12
- **Cooldown:** 2 turns
- **Animation:** Concentrated dive (`v`, `V`, `Λ`, `▼`)
- **Targeting:** Single enemy unit

### 3. Emetic Flange
Close-range explosion of birds bursting outward in all directions.

- **Range:** 0 (self-centered)
- **Area:** All adjacent tiles (8 surrounding tiles)
- **Damage:** 6
- **Cooldown:** 4 turns
- **Animation:** Explosive burst (`*`, `#`, `@`, `&`)
- **Special:** Damages and pushes enemy units back 1 tile; friendly units are unaffected
- **Targeting:** Automatically centered on the unit

## Team Composition Considerations

### Strategic Trade-offs
- **One FOWL CONTRIVANCE:** Maximum reliability for instant-kills (100% chance)
- **Two FOWL CONTRIVANCE:** Higher overall damage output but reduced instant-kill reliability (50% chance)
- **Three FOWL CONTRIVANCE:** Highest potential damage output but lowest instant-kill reliability (25% chance)

### Synergies
- **MARROW_CONDENSER:** Provides defensive walls to protect the fragile FOWL CONTRIVANCE
- **GLAIVEMAN:** Can use Pry to create space and protect FOWL CONTRIVANCE
- **GRAYMAN:** Can set up positioning for FOWL CONTRIVANCE's area attacks

## Gameplay Style
- **Glass Cannon:** Extremely high damage output but very fragile
- **Positioning:** Requires careful placement to maximize effectiveness
- **High Risk/Reward:** Can turn the tide of battle but easily eliminated
- **Team Support:** Benefits greatly from protection by tankier allies

## Weaknesses
- Extremely low health makes it vulnerable to any attack
- No mobility or escape abilities
- No defensive options
- Passive ability becomes less reliable with multiple FOWL CONTRIVANCE units

## Implementation Notes

The Flock Loyalty mechanic should be implemented as follows:

```python
def check_wretched_decension_chance(self, game):
    """Calculate chance of Wretched Decension triggering based on number of allied FOWL CONTRIVANCE units."""
    # Count allied FOWL CONTRIVANCE units
    allied_fowl_count = 0
    for unit in game.units:
        if unit.is_alive() and unit.player == self.player and unit.type == UnitType.FOWL_CONTRIVANCE:
            allied_fowl_count += 1
    
    # Calculate chance based on count
    if allied_fowl_count == 1:
        return 1.0  # 100% chance
    elif allied_fowl_count == 2:
        return 0.5  # 50% chance
    elif allied_fowl_count >= 3:
        return 0.25  # 25% chance
    
    return 1.0  # Fallback (should never happen)
```

When a unit is reduced to critical health status by FOWL CONTRIVANCE, the game should:
1. Determine how many FOWL CONTRIVANCE units the attacking player has
2. Calculate the appropriate chance for instant-kill
3. Roll a random number to determine if the passive triggers
4. Apply the appropriate visual effect and messaging

This creates meaningful decisions around team composition while maintaining the FOWL CONTRIVANCE's identity as a devastating but vulnerable nuker.