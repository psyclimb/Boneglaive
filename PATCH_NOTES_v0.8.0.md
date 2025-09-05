# Boneglaive v0.8.0 Patch Notes

## New Unit: DERELICTIONIST

The DERELICTIONIST is a psychological abandonment therapist who weaponized distance-based therapeutic techniques into a support system. This healer specializes in trauma processing, protective partitioning, and abandonment therapy through controlled dissociation. Manipulates interpersonal distance for healing effects and status management.

**Role**: Utility / Healer  
**Difficulty**: ***  
**Stats**: HP: 18, Attack: 2, Defense: 0, Movement: 3, Range: 1

### DERELICTIONIST Skills
- **SEVERANCE (Passive)**: Allows skill use followed by enhanced movement (+1 range)
- **VAGAL RUN (Active)**: Immediate effect plus delayed abreaction after 3 turns
- **DERELICT (Active)**: Distance-based damage/healing (closer = damage, farther = healing)
- **PARTITION (Active)**: Shield with emergency fatal damage blocking and displacement

---

## Enhanced Visual Effects

### INTERFERER Skill Animations
- **SCALAR NODE**: New 16-frame animation featuring scalar standing wave erupting in geyser of sparks with color flashing effects
- **NEURAL SHUNT**: Complex 4-stage animation system showing three radio wave streams converging, surging through nervous system, then confusion flashing

### Animation System Improvements
- Enhanced color flashing sequences for critical abilities
- Multi-stage animation support for complex skill effects
- Improved visual feedback for skill activation

---

## Balance Changes

### Unit Statistics
- **INTERFERER**: Base attack reduced from 4 to 3
- **HEINOUS VAPOR**: HP reduced from 10 to 1

### Skill Adjustments
- **GAS MACHINIST - SAFT-E-GAS**: Reworked from making units untargetable to granting +1 defense to allied units in vapor cloud
- **DELPHIC APPRAISER - AUCTION CURSE**: 
  - Removed healing effect
  - Cooldown reduced from 4 to 3 turns
- **INTERFERER - SCALAR NODE**: Changed from pierce damage to regular damage (respects defense)
- **FOWL CONTRIVANCE - PARABOL**: Minimum range increased from radius 1 to 3 around the unit for self-damage protection

---

## Immunity System Overhaul

### GRAYMAN Stasiality Interactions
- **VAGAL RUN**: GRAYMAN now only immune to abreaction effect, still receives immediate damage/effects
- **DERELICT**: GRAYMAN immune to displacement and dereliction status, but can still receive healing
- **PARTITION**: GRAYMAN completely immune to all effects
- Added "due to Stasiality" immunity messages for clarity

---

## Bug Fixes

### MANDIBLE FOREMAN
- **EXPEDITE**: Fixed IndexError when no valid path exists by adding safety checks for empty path_positions

### Message System Improvements
- Updated all displacement messages to include both "from" and "to" coordinates
- Enhanced coordinate tracking for MARROW DIKE and DIVINE DEPRECIATION displacement effects
- Removed redundant "Marrow Dike will create walls around the perimeter" message
- Updated NEURAL SHUNT coordination message: "coordinates neural interference transmission" to "coordinates a neural interference triangulation"

---

## Help System Enhancements

### Unit Difficulty Ratings
All units now include difficulty ratings from * (1 star) to ***** (5 stars):

- ***** (1 Star): GRAYMAN
- ***** (2 Stars): GLAIVEMAN, MANDIBLE FOREMAN, INTERFERER
- ***** (3 Stars): FOWL CONTRIVANCE, DERELICTIONIST, MARROW CONDENSER
- ***** (4 Stars): DELPHIC APPRAISER
- ***** (5 Stars): GAS MACHINIST

### Role Updates
- **GRAYMAN**: Added "Summoner" role
- **GAS MACHINIST**: Added "Healer" role
- **DERELICTIONIST**: Added "Healer" role

### Help Page Corrections
- **INTERFERER**: Updated help page to reflect SCALAR NODE no longer pierces defense
- **FOWL CONTRIVANCE**: Corrected attack value display from 5 to 4

---

## Technical Improvements

### Version Updates
- Updated version number to v0.8.0 across all files:
  - `setup.py`
  - `boneglaive/__init__.py`
  - `README.md`
  - `boneglaive/ui/menu_ui.py`

### Code Quality
- Enhanced error handling for edge cases in movement and pathfinding
- Improved message clarity and consistency across all skill descriptions
- Refined status effect application logic for immunity interactions

---

## Quality of Life

### Message Clarity
- Improved displacement messages with coordinate information
- Enhanced skill description clarity in help pages
- Standardized immunity notification messages
- Removed extraneous or confusing status messages

### User Experience
- Difficulty ratings help players choose appropriate units for their skill level
- Enhanced role descriptions provide clearer unit function understanding
- Improved visual feedback for complex skill interactions

---

## Removed Features

- **SAFT-E-GAS**: Untargetable effect (replaced with +1 defense)
- **AUCTION CURSE**: Healing component
- **SCALAR NODE**: Pierce damage capability
- Various redundant or unclear status messages

---

*These changes represent a significant balance pass focusing on unit diversity, visual clarity, and gameplay accessibility. The addition of the DERELICTIONIST introduces new healing and positioning tactics to the tactical combat system.*