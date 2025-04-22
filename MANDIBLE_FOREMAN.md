# MANDIBLE FOREMAN

## Overview
A specialist unit that combines control mechanics with team support capabilities.

## Passive Ability
**Viceroy**: When the MANDIBLE FOREMAN attacks a unit, they are trapped in his mechanical jaws. The trapped unit's move value is reduced to 0 and they cannot activate skills as long as they are trapped. The MANDIBLE FOREMAN applies attack damage to the trapped unit at the start of every combat phase. If the MANDIBLE FOREMAN discharges, perishes, moves, or performs any other action (except Recalibrate), the trapped effect on the unit ends.

## Active Abilities

1. **Discharge** - The FOREMAN releases a trapped unit, throwing them 2-3 tiles in a chosen direction. Deals moderate damage on impact with walls/obstacles. Cooldown: 2 turns.

2. **Recalibrate** - FOREMAN adjusts his mechanical jaws, increasing his attack value for 2 turns. This attack bonus also increases the damage from his Viceroy trap. If a unit is trapped, also applies a defensive debuff to them. Unlike other actions, Recalibrate does not release trapped units. Cooldown: 3 turns.

3. **Site Inspection** - FOREMAN surveys a 3x3 area, revealing hidden units and studying structure. Grants movement and attack bonuses to FOREMAN and all allies in the inspection area when adjacent to walls/structures for 2 turns. Cooldown: 4 turns.

## Implementation Notes
- Will need trap state tracking for targeted units
- Damage application at combat phase start
- Special animation for trapped units
- Range indicators for Discharge targeting
- Area effect implementation for Site Inspection