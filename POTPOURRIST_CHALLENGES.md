# POTPOURRIST Implementation Challenges

This document outlines the technical challenges involved in implementing the POTPOURRIST unit, ranked by difficulty.

## HIGH DIFFICULTY

### 1. Demilune Damage Halving (Option 1 Approach)

**The Problem:**
The `hp` setter (units.py:580) doesn't know WHO is dealing damage - it only receives the new HP value. Demilune debuff requires knowing the attacker to determine if damage should be halved.

**Solution: Global Attacker Context**
- Add `game.current_attacker` attribute to Game class
- Before any damage dealing:
  - Set `game.current_attacker = attacking_unit`
  - Apply damage: `target.hp = new_value`
  - Clear `game.current_attacker = None`
- In hp setter (units.py:580), after PRT calculation:
  - Check if `self._game` and `self._game.current_attacker` exist
  - Check if attacker has `demilune_debuffed_by` pointing to a POTPOURRIST
  - Check if that POTPOURRIST is `self` (the defender)
  - If all true: halve the damage

**Locations Requiring Changes:**
- Game engine basic attack damage
- All skill damage applications (9+ skill modules)
- Trap/environmental damage
- Status effect damage (shrapnel, etc.)

**Complexity:** Requires touching many files, but the pattern is consistent once established.

---

### 2. Granite Gavel Taunt Tracking

**The Problem:**
Need to track whether a taunted unit attacked/skilled the POTPOURRIST during their turn, then apply healing if they didn't.

**Implementation Plan:**

**Unit Properties:**
- `taunted_by` (Unit reference or None)
- `taunt_duration` (int, turns remaining)
- `taunt_responded_this_turn` (bool, reset each turn)

**When Granite Gavel Hits:**
```python
target.taunted_by = potpourrist_unit
target.taunt_duration = 1  # or 2 if enhanced
target.taunt_responded_this_turn = False
```

**During Combat (Attacks/Skills):**
```python
# After any attack or skill
if attacker.taunted_by == target:
    attacker.taunt_responded_this_turn = True
```

**At End of Taunted Unit's Turn:**
```python
if not unit.taunt_responded_this_turn:
    unit.taunted_by.heal(4)  # Direct heal, bypasses prevention

unit.taunt_duration -= 1
if unit.taunt_duration <= 0 or unit.taunt_responded_this_turn:
    unit.taunted_by = None
    unit.taunt_duration = 0

unit.taunt_responded_this_turn = False  # Reset for next turn
```

**Integration Points:**
- Basic attack code (set response flag)
- All skill code (set response flag)
- Turn end resolution (check flag, apply heal, decrement duration)

**Complexity:** Requires integration across attack system, skill system, and turn management. Multiple touch points but straightforward logic.

---

## MODERATE DIFFICULTY

### 3. Potpourri Enhancement System

**The Challenge:**
Track potpourri state and apply different enhancements to different skills when consumed.

**Implementation:**
- Add `potpourri_held` (bool) to POTPOURRIST units
- **Commingle skill:**
  - `can_use()` checks `not user.potpourri_held`
  - `use()` sets `user.potpourri_held = True`
  - Cooldown = 0, self-targeting
- **Damaging skills (Demilune, Granite Gavel):**
  - Check `user.potpourri_held` in `use()` method
  - Apply enhanced effects if True
  - Set `user.potpourri_held = False` after use
- **Passive skill (Melange Eminence):**
  - Check `user.potpourri_held`
  - Heal 3 HP if True, 1 HP if False

**Enhancement Effects:**
- Demilune: Damage 3→4, adds defense halving to debuff
- Granite Gavel: Duration 1→2 turns

**Complexity:** Requires coordination across multiple skills but follows a consistent pattern.

---

### 4. Defense Halving (Enhanced Demilune)

**The Challenge:**
When POTPOURRIST attacks a unit with enhanced Demilune debuff, their defense should be halved during damage calculation.

**Implementation:**
- Add `demilune_defense_halved` (bool) to unit properties
- Set by enhanced Demilune skill
- In POTPOURRIST's attack damage calculation:
  ```python
  if target.demilune_debuffed_by == self and target.demilune_defense_halved:
      effective_defense = target.defense // 2
  else:
      effective_defense = target.defense
  ```

**Complexity:** Must integrate into basic attack damage calculation in game engine.

---

### 5. Melange Eminence Healing Bypass

**The Challenge:**
Passive healing must bypass Auction Curse and all other healing prevention.

**Implementation:**
- Apply at start of POTPOURRIST's turn
- Bypass auction curse by directly modifying HP (skip `heal()` method):
  ```python
  heal_amount = 3 if user.potpourri_held else 1
  old_hp = user._hp
  user._hp = min(user.max_hp, user._hp + heal_amount)
  actual_heal = user._hp - old_hp
  # Add message log entry
  ```

**Complexity:** Straightforward bypass of normal healing system.

---

## LOW-MODERATE DIFFICULTY

### 6. Demilune Arc Pattern

**The Challenge:**
Hit 5 tiles in a forward arc based on targeting direction.

**Implementation:**
```
X X X
X P X
```
- Determine forward direction from skill target position
- Calculate 5 tiles: forward-left diagonal, forward, forward-right diagonal, left, right
- Iterate through arc tiles, find enemy units only
- Apply damage (3 base, 4 enhanced) to each
- Apply Demilune debuff to each hit enemy

**Complexity:** Similar to existing AoE skills (Autoclave, Big Arc). Pattern matching and iteration.

---

### 7. Status Effect Duration Tracking

**The Challenge:**
Track multiple new status effects and their durations.

**New Unit Properties (add to `Unit.__init__`):**
- `demilune_debuffed_by = None` (Unit reference)
- `demilune_debuff_duration = 0` (int)
- `demilune_defense_halved = False` (bool)
- `taunted_by = None` (Unit reference)
- `taunt_duration = 0` (int)
- `taunt_responded_this_turn = False` (bool)
- `potpourri_held = False` (bool, POTPOURRIST only)

**Turn End Processing:**
- Decrement durations
- Clean up expired effects (set references to None, bools to False)

**Complexity:** Standard status effect tracking following existing patterns.

---

## LOW DIFFICULTY

### 8. Basic Unit Setup

**Required Changes:**

**constants.py:**
```python
class UnitType(Enum):
    # ... existing types ...
    POTPOURRIST = 12

UNIT_STATS = {
    # ... existing stats ...
    UnitType.POTPOURRIST: (28, 4, 0, 2, 1),  # HP, ATK, DEF, MOVE, RANGE
}

UNIT_SYMBOLS = {
    # ... existing symbols ...
    UnitType.POTPOURRIST: 'P',
}

ATTACK_EFFECTS = {
    # ... existing effects ...
    UnitType.POTPOURRIST: 'I',  # Pedestal strike
}
```

**Create `boneglaive/game/skills/potpourrist.py`:**
- MelangeEminence (PassiveSkill)
- CommungleSkill (ActiveSkill)
- DemiluneSkill (ActiveSkill)
- GraniteGavelSkill (ActiveSkill)

**registry.py:**
```python
from boneglaive.game.skills.potpourrist import (
    MelangeEminence, CommungleSkill, DemiluneSkill, GraniteGavelSkill
)

UNIT_SKILLS = {
    # ... existing skills ...
    "POTPOURRIST": {
        "passive": MelangeEminence(),
        "active": [CommungleSkill(), DemiluneSkill(), GraniteGavelSkill()]
    }
}
```

**Complexity:** Straightforward additions following existing patterns.

---

## Summary

**Most Challenging:**
1. Demilune damage halving (requires global attacker context)
2. Granite Gavel taunt tracking (multi-system integration)

**Moderate Challenges:**
3. Potpourri enhancement system
4. Defense halving
5. Healing bypass

**Easier Tasks:**
6. Arc pattern implementation
7. Status effect tracking
8. Basic unit setup

**Estimated Total Effort:** Medium-Large (1-2 days of focused implementation)
