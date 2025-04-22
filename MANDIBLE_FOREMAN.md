# MANDIBLE FOREMAN

## Overview
A specialist unit that combines control mechanics with team support capabilities.

## Passive Ability
**Viseroy**: When the MANDIBLE FOREMAN attacks a unit, they are trapped in his mechanical jaws. The trapped unit's move value is reduced to 0 and they cannot activate skills as long as they are trapped. The MANDIBLE FOREMAN applies attack damage to the trapped unit at the start of every combat phase. If the MANDIBLE FOREMAN discharges, perishes, moves, or performs any other action, the trapped effect on the unit ends.

## Active Abilities

1. **Discharge** - The FOREMAN releases a trapped unit, throwing them 2-3 tiles in a chosen direction. Deals moderate damage on impact with walls/obstacles. Cooldown: 2 turns.

2. **Site Inspection** - FOREMAN surveys a 3x3 area, revealing hidden units and studying structure. Grants movement and attack bonuses to FOREMAN and all allies in the inspection area when adjacent to walls/structures. Cooldown: 4 turns.

3. **Jawline** - Deploys a network of smaller mechanical jaws connected by cables in a 3×3 area around the FOREMAN. All enemy units in the area have their movement reduced by 1 and cannot use movement-based skills for 3 turns. Cooldown: 5 turns.

## Implementation Notes
- Will need trap state tracking for targeted units
- Damage application at combat phase start
- Special animation for trapped units
- Range indicators for Discharge targeting
- Area effect implementation for Site Inspection