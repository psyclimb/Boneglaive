# POTPOURRIST Implementation Plan

This document provides a step-by-step implementation plan for adding the POTPOURRIST unit to Boneglaive.

## Implementation Order

Tasks are ordered to minimize dependencies and allow for incremental testing.

---

## Phase 1: Foundation (Low Risk)

### Task 1.1: Add Unit Type and Constants
**File:** `boneglaive/utils/constants.py`

**Changes:**
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

**Test:** Import constants, verify no errors.

---

### Task 1.2: Add Status Effect Properties to Unit Class
**File:** `boneglaive/game/units.py`

**Changes in `Unit.__init__()`:**
```python
# POTPOURRIST-related status effects
self.demilune_debuffed_by = None  # Reference to POTPOURRIST that applied debuff
self.demilune_debuff_duration = 0  # Turns remaining
self.demilune_defense_halved = False  # Enhanced Demilune effect
self.taunted_by = None  # Reference to POTPOURRIST that applied taunt
self.taunt_duration = 0  # Turns remaining
self.taunt_responded_this_turn = False  # Track if unit attacked/skilled POTPOURRIST
self.potpourri_held = False  # POTPOURRIST only - tracks enhancement state
```

**Test:** Create unit, verify properties exist.

---

### Task 1.3: Add Global Attacker Context to Game Class
**File:** `boneglaive/game/engine.py`

**Changes in `Game.__init__()`:**
```python
# Track current attacker for damage modifiers (Demilune debuff)
self.current_attacker = None
```

**Test:** Create game, verify property exists.

---

## Phase 2: Skills Implementation (Core Mechanics)

### Task 2.1: Create Passive Skill - Melange Eminence
**File:** `boneglaive/game/skills/potpourrist.py` (new file)

**Implementation:**
```python
class MelangeEminence(PassiveSkill):
    def __init__(self):
        super().__init__(
            name="Melange Eminence",
            key="M",
            description="Heals 1 HP every turn (3 HP while holding potpourri). Cannot be prevented by any effect."
        )

    def apply_passive(self, user, game=None):
        # Bypass all healing prevention by directly modifying HP
        heal_amount = 3 if user.potpourri_held else 1
        old_hp = user._hp
        user._hp = min(user.max_hp, user._hp + heal_amount)
        actual_heal = user._hp - old_hp

        if actual_heal > 0:
            from boneglaive.utils.message_log import message_log, MessageType
            message_log.add_message(
                f"{user.get_display_name()} regenerates {actual_heal} HP",
                MessageType.ABILITY,
                player=user.player
            )
```

**Test:** Apply passive, verify healing occurs even with auction_curse_no_heal.

---

### Task 2.2: Create Active Skill 1 - Commingle
**File:** `boneglaive/game/skills/potpourrist.py`

**Implementation:**
```python
class CommungleSkill(ActiveSkill):
    def __init__(self):
        super().__init__(
            name="Commingle",
            key="1",
            description="Creates potpourri that enhances next skill and increases Melange Eminence to 3 HP/turn.",
            skill_type=SkillType.ACTIVE,
            target_type=TargetType.SELF,
            cooldown=0,
            range_=0
        )

    def can_use(self, user, target_pos=None, game=None):
        if not super().can_use(user, target_pos, game):
            return False
        # Can only use when NOT already holding potpourri
        return not user.potpourri_held

    def use(self, user, target_pos=None, game=None):
        if not self.can_use(user, target_pos, game):
            return False

        user.potpourri_held = True

        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{user.get_display_name()} creates a potpourri blend",
            MessageType.ABILITY,
            player=user.player
        )

        return True
```

**Test:** Use Commingle, verify potpourri_held flag set, verify can't use twice.

---

### Task 2.3: Create Active Skill 2 - Demilune (Basic Version)
**File:** `boneglaive/game/skills/potpourrist.py`

**Implementation:**
- Determine forward arc (5 tiles) based on target direction
- Hit all enemy units in arc
- Deal damage (3 base, 4 if potpourri_held)
- Apply Demilune debuff to hit enemies
- Consume potpourri if held

**Arc Pattern Logic:**
```python
def _get_arc_tiles(self, user_y, user_x, target_y, target_x):
    """Get 5 tiles in forward arc based on target direction."""
    # Determine primary direction
    dy = target_y - user_y
    dx = target_x - user_x

    # Normalize direction
    # Return 5 tiles: forward, forward-left, forward-right, left, right
    # Pattern:
    # X X X
    # X P X
```

**Test:** Use Demilune on various directions, verify arc pattern, verify damage.

---

### Task 2.4: Create Active Skill 3 - Granite Gavel (Basic Version)
**File:** `boneglaive/game/skills/potpourrist.py`

**Implementation:**
- Range 3 single target attack
- Deal 4 damage
- Apply taunt (duration = 1, or 2 if potpourri_held)
- Consume potpourri if held

**Test:** Use Granite Gavel, verify taunt applied, verify duration varies with potpourri.

---

### Task 2.5: Register Skills
**File:** `boneglaive/game/skills/registry.py`

**Changes:**
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

**Test:** Create POTPOURRIST unit, verify skills assigned.

---

## Phase 3: Damage Halving System (High Complexity)

### Task 3.1: Implement Global Attacker Context Pattern
**Files:** Multiple (game engine, all skill modules)

**Pattern to Apply:**
```python
# Before dealing damage:
game.current_attacker = attacking_unit
target.hp = target.hp - damage
game.current_attacker = None
```

**Locations:**
1. `boneglaive/game/engine.py` - basic attack damage
2. All skill modules that deal damage:
   - `glaiveman.py` (Pry, Vault, Judgement, Autoclave)
   - `mandible_foreman.py` (Discharge, Site Inspection, Jawline)
   - `grayman.py` (Delta Config, Estrange)
   - `marrow_condenser.py` (Ossify, Marrow Dike, Bone Tithe)
   - `fowl_contrivance.py` (Gaussian Dusk, Big Arc, Fragcrest)
   - `gas_machinist.py` (Enbroachment Gas, Saft-E-Gas, Diverge)
   - `delphic_appraiser.py` (Market Futures, Auction Curse, Divine Depreciation)
   - `interferer.py` (Neural Shunt, Karrier Rave, Scalar Node)
   - `derelictionist.py` (Vagal Run, Derelict)
   - `potpourrist.py` (Demilune, Granite Gavel)
3. Trap/environmental damage (Viseroy trap, Marrow Dike)
4. Status effect damage (shrapnel)

**Approach:**
- Start with basic attacks in engine.py
- Add to POTPOURRIST skills (Demilune, Granite Gavel)
- Gradually add to other skill modules
- Test incrementally

---

### Task 3.2: Implement Damage Halving in HP Setter
**File:** `boneglaive/game/units.py`

**Changes in `hp` property setter (around line 663, after PRT calculation):**
```python
# After PRT processing, before final damage application:

# Check for Demilune damage halving
if (self._game and
    hasattr(self._game, 'current_attacker') and
    self._game.current_attacker and
    hasattr(self, 'demilune_debuffed_by') and
    self.demilune_debuffed_by and
    self.demilune_debuffed_by == self):

    # Attacker has Demilune debuff against this POTPOURRIST
    actual_damage = actual_damage // 2

    from boneglaive.utils.message_log import message_log, MessageType
    message_log.add_message(
        f"{self._game.current_attacker.get_display_name()}'s attack is weakened by Demilune",
        MessageType.ABILITY,
        player=self.player
    )
```

**Test:**
1. Apply Demilune debuff manually
2. Attack POTPOURRIST, verify damage halved
3. Attack from non-debuffed unit, verify normal damage

---

### Task 3.3: Implement Defense Halving in Attack Calculation
**File:** `boneglaive/game/engine.py` (or wherever attack damage is calculated)

**Changes:**
```python
# In attack damage calculation:
effective_defense = target.defense

# Check for Demilune defense halving
if (attacker.type == UnitType.POTPOURRIST and
    hasattr(target, 'demilune_debuffed_by') and
    target.demilune_debuffed_by == attacker and
    hasattr(target, 'demilune_defense_halved') and
    target.demilune_defense_halved):
    effective_defense = effective_defense // 2

damage = max(1, attacker_stats['attack'] - effective_defense)
```

**Test:**
1. Apply enhanced Demilune debuff manually
2. POTPOURRIST attacks target, verify defense halved
3. Other unit attacks target, verify normal defense

---

## Phase 4: Taunt System (High Complexity)

### Task 4.1: Implement Taunt Response Tracking
**File:** `boneglaive/game/engine.py`

**Changes in attack/skill resolution:**
```python
# After any attack or skill use:
if (attacker.taunted_by and
    attacker.taunted_by == target and
    target.type == UnitType.POTPOURRIST):
    attacker.taunt_responded_this_turn = True
```

**Locations:**
- Basic attack resolution
- Skill resolution (may need to add to each skill's use() method)

---

### Task 4.2: Implement Taunt Resolution at Turn End
**File:** `boneglaive/game/engine.py`

**Changes in turn end logic:**
```python
# At end of turn, for each unit:
if unit.taunted_by and unit.taunt_duration > 0:
    if not unit.taunt_responded_this_turn:
        # POTPOURRIST heals
        unit.taunted_by._hp = min(
            unit.taunted_by.max_hp,
            unit.taunted_by._hp + 4
        )
        from boneglaive.utils.message_log import message_log, MessageType
        message_log.add_message(
            f"{unit.taunted_by.get_display_name()} heals 4 HP from ignored taunt",
            MessageType.ABILITY,
            player=unit.taunted_by.player
        )

    # Decrement duration
    unit.taunt_duration -= 1
    if unit.taunt_duration <= 0 or unit.taunt_responded_this_turn:
        unit.taunted_by = None
        unit.taunt_duration = 0

    # Reset flag for next turn
    unit.taunt_responded_this_turn = False
```

**Test:**
1. Apply taunt manually
2. Target attacks POTPOURRIST - verify no heal, taunt ends
3. Target attacks someone else - verify POTPOURRIST heals, check duration
4. Enhanced taunt (2 turns) - verify persists for 2 turns if not responded to

---

## Phase 5: Duration Tracking and Cleanup

### Task 5.1: Implement Status Effect Duration Decrement
**File:** `boneglaive/game/engine.py`

**Changes in turn end logic:**
```python
# Decrement Demilune debuff
if unit.demilune_debuff_duration > 0:
    unit.demilune_debuff_duration -= 1
    if unit.demilune_debuff_duration <= 0:
        unit.demilune_debuffed_by = None
        unit.demilune_defense_halved = False
```

**Test:** Apply debuff with duration, verify decrements and clears.

---

## Phase 6: Integration and Polish

### Task 6.1: Add to Recruitment System
**File:** `boneglaive/game/recruitment.py` or wherever unit selection happens

Ensure POTPOURRIST appears in unit selection menus.

---

### Task 6.2: AI Integration
**File:** `boneglaive/ai/simple_ai.py`

**Changes:**
- AI should recognize POTPOURRIST as high-value target (high HP)
- AI should consider Demilune debuff when choosing targets
- AI should respond to taunt (natural behavior - it will choose to attack to avoid penalty)

---

### Task 6.3: UI Indicators
**File:** `boneglaive/ui/ui_components.py` or relevant UI files

**Add indicators for:**
- Potpourri held status (visual indicator on POTPOURRIST)
- Demilune debuff (show on affected units)
- Taunt status (show on taunted units)

---

### Task 6.4: Testing and Balance

**Test Cases:**
1. **Melange Eminence:**
   - Heals 1 HP per turn normally
   - Heals 3 HP per turn with potpourri
   - Bypasses Auction Curse

2. **Commingle:**
   - Can be used when no potpourri held
   - Cannot be used when potpourri held
   - Cooldown = 0

3. **Demilune:**
   - Hits 5 tiles in forward arc
   - Only hits enemies
   - Damage: 3 base, 4 enhanced
   - Applies debuff that halves damage to POTPOURRIST
   - Enhanced adds defense halving
   - Duration: 2 turns
   - Consumes potpourri

4. **Granite Gavel:**
   - Range 3 single target
   - Damage: 4
   - Applies taunt (1 turn base, 2 turns enhanced)
   - POTPOURRIST heals 4 HP if not responded to
   - Taunt ends early if responded to
   - Consumes potpourri

5. **Full Rotation:**
   - Commingle → Enhanced Demilune → Verify effects
   - Commingle → Enhanced Granite Gavel → Verify 2-turn taunt
   - Verify potpourri consumed after skill use

6. **Edge Cases:**
   - POTPOURRIST dies while taunt active
   - Multiple POTPOURRISTs with overlapping debuffs
   - Demilune debuff on units attacking each other

---

## Phase 7: Documentation

### Task 7.1: Update Help Documentation
Add POTPOURRIST to in-game help system with skill descriptions.

### Task 7.2: Update README
Add POTPOURRIST to unit roster in README.md if applicable.

---

## Estimated Timeline

- **Phase 1 (Foundation):** 1-2 hours
- **Phase 2 (Skills):** 3-4 hours
- **Phase 3 (Damage Halving):** 4-6 hours (most time-consuming)
- **Phase 4 (Taunt System):** 3-4 hours
- **Phase 5 (Duration Tracking):** 1-2 hours
- **Phase 6 (Integration):** 2-3 hours
- **Phase 7 (Documentation):** 1 hour

**Total Estimated Time:** 15-22 hours (2-3 days of focused work)

---

## Risk Mitigation

**High Risk Areas:**
1. Damage halving system (many files to modify)
2. Taunt tracking (multi-system integration)

**Mitigation Strategies:**
- Implement incrementally
- Test after each phase
- Use logging extensively during development
- Create test scenarios for edge cases
- Keep backup of working code before major changes

---

## Success Criteria

- [ ] POTPOURRIST appears in unit selection
- [ ] All skills function as described in design doc
- [ ] Potpourri enhancement system works correctly
- [ ] Demilune damage halving works for all damage sources
- [ ] Defense halving works when POTPOURRIST attacks debuffed units
- [ ] Taunt tracking works correctly (heal when ignored)
- [ ] Enhanced Granite Gavel extends taunt to 2 turns
- [ ] Melange Eminence bypasses healing prevention
- [ ] Status effects have correct durations
- [ ] No crashes or errors in normal gameplay
- [ ] AI can use POTPOURRIST effectively
- [ ] UI shows status effects clearly
