# Unit Help Page Revamp TODO

## Completed ✓
- [x] POTPOURRIST
- [x] INTERFERER
- [x] DERELICTIONIST
- [x] DELPHIC_APPRAISER
- [x] GAS_MACHINIST

## Remaining Units to Revamp

### Priority Order (by complexity/importance)

1. **GRAYMAN** - Unique anomaly unit with reality distortion
   - Skills: Effluvium Lathe (passive), Broaching, Saft-E-Gas, Diverge
   - Focus: Explain vapor types, charge system, diverge splitting mechanic
   - Note: May need to update HEINOUS_VAPOR help pages for different vapor types

3. **GRAYMAN** - Unique anomaly unit with reality distortion
   - Skills: Stasiality (passive), Echo, Marrow Wall, Fragcrest
   - Focus: Explain immunity mechanics, echo copies, wall creation, knockback

4. **MARROW_CONDENSER** - Bone manipulation specialist
   - Skills: Slough (passive), Bone Tithe, Marrow Salve, Ossify
   - Focus: Clarify bone resource mechanics, defense buffs, petrification

5. **FOWL_CONTRIVANCE** - Bird flock artillery unit
   - Skills: Plummet (passive), Peck, Artillery Strike, Roost
   - Focus: Explain flock mechanics, long-range attacks, roosting

6. **MANDIBLE_FOREMAN** - Trap/control specialist
   - Skills: Jawline (passive), Snap Trap, Excavate, Mire
   - Focus: Clarify trap mechanics, terrain control, immobilization

7. **GLAIVEMAN** - Basic melee fighter (starter unit)
   - Skills: Charge (passive), Shield Bash, Power Strike, Rally
   - Focus: Simple, clear descriptions for new players

## HEINOUS_VAPOR Subtypes
- **BROACHING GAS** (DoT vapor)
- **SAFT-E-GAS** (Healing/cleansing vapor)
- **COOLANT GAS** (from Diverge)
- **CUTTING GAS** (from Diverge)

Note: These may need individual help page updates after GAS_MACHINIST is complete.

## Revamp Guidelines
For each unit, follow the pattern established with POTPOURRIST/INTERFERER/DERELICTIONIST:

### Part 1: Rewrite Descriptions
- **Overview**: Vivid imagery, explain core mechanics and playstyle
- **Each Skill**:
  - Explain WHAT happens mechanically
  - Explain HOW it happens thematically/visually
  - Include specific numbers and ranges
  - Clarify any complex interactions

### Part 2: Standardize Details Sections
- Remove all redundant information already in description
- Include status effect symbols: `Effect: StatusName (symbol) (duration)`
- Only include: Type, Range (if applicable), Target (if needed), Damage (if applicable), Effect (with symbol), Cooldown, Special (unique mechanics only)
- If skill doesn't apply status effect, don't include Effect line

### Verification Checklist
- [ ] Read actual skill code to verify accuracy
- [ ] Check for distance-based mechanics
- [ ] Verify status effect names and symbols (ui_renderer.py)
- [ ] Confirm cooldowns, ranges, damage values
- [ ] Test that description matches implementation

## Notes
- Always verify mechanics against actual code before writing
- Use proper grammar and complete sentences
- Maintain consistent format across all units
- Focus on player understanding over technical jargon
