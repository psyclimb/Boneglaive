# POTPOURRIST Message Log Documentation & Proposals

## Overview
This document catalogs all message log entries for the POTPOURRIST unit's skills and proposes thematic improvements to better capture the character's potpourri aromatics, granite weight, and tank presence.

---

## Current Message Log Entries (Categorized)

### **1. MELANGE EMINENCE (Passive Skill)**

**Purpose**: Passive healing that triggers at start of turn (1 HP normally, 2 HP with potpourri)

#### Current Messages
- **Location**: `boneglaive/game/skills/potpourrist.py:83-87`
- **Trigger**: Start of POTPOURRIST's turn when healing > 0
- **Message**: 
- **Type**: MessageType.ABILITY

#### Proposed Alternative
- **RECOMMENDED**: `"{unit} inhales the restorative melange for ({actual_heal} HP)"`
- **Rationale**: Emphasizes the potpourri scent theme, shows healing comes from breathing the blend

---

### **2. INFUSE (Active Skill 1 - Potpourri Creation)**

**Purpose**: Self-targeting skill that creates potpourri (enhances next skill + boosts passive healing)

#### Current Messages

**Queue Phase** (potpourrist.py:132-136)
- **Trigger**: When player selects Infuse during action selection
- **Message**: `"{unit} prepares a potpourri blend"`
- **Type**: MessageType.ABILITY
- **Proposed**: `"{unit} begins mixing a potent blend of potpourri"`

**Execute Start** (potpourrist.py:146-150)
- **Trigger**: During combat phase when Infuse executes
- **Message**: `"{unit} begins infusing potpourri"`
- **Type**: MessageType.ABILITY
- **Proposed**: `"{unit} infuses the blend with aromatic power"`

**Execute Complete** (potpourrist.py:180-184)
- **Trigger**: After animation, when potpourri_held flag is set
- **Message**: `"{unit} creates a potpourri blend!"`
- **Type**: MessageType.ABILITY
- **Proposed**: `"{unit} holds a fuming potpourri blend"`

**Rationale**: More vivid sensory language about the mixing process and the powerful aromatics

---

### **3. DEMILUNE (Active Skill 2 - Arc Swing with Lunacy)**

**Purpose**: Forward arc attack (5 tiles) that deals damage and applies Lunacy debuff (damage halving + defense halving if enhanced)

#### Current Messages

**Queue** (potpourrist.py:287-291)
- **Message**: `"{unit} readies to swing the granite pedestal in an arc"`
- **Proposed**: `"{unit} readies a mighty crescent swing"`

**Execute** (potpourrist.py:358-362)
- **Message**: `"{unit} swings the granite pedestal in an arc"`
- **Proposed**: `"{unit} sweeps the granite pedestal in a crescent arc"`

**Damage Per Target** (potpourrist.py:409-413)
- **Message**: `"{target} takes #DAMAGE_{actual_damage}# damage from Demilune"`
- **Type**: MessageType.COMBAT
- **Proposed**: Keep as-is (standard damage format)

**Status Applied** (potpourrist.py:439-443)
- **Trigger**: When target is NOT immune to effects
- **Message**: `"{target} is afflicted with Lunacy"`
- **Type**: MessageType.ABILITY
- **Proposed**: `"{target} has their damage eclipsed"`

**Status Immunity** (potpourrist.py:445-449)
- **Trigger**: When target has Stasiality (GRAYMAN passive)
- **Message**: `"{target} is immune to Lunacy due to Stasiality"`
- **Proposed**: Keep as-is (clear explanation)

**No Targets Hit** (potpourrist.py:453-458) <--remove this messaging
- **Message**: `"The swing hits no enemies!"`
- **Type**: MessageType.WARNING
- **Proposed**: `"The crescent arc strikes only air!"`

**Status Expiration** (engine.py:3525-3529) <--remove this messaging if other status effects do not have messages when they fall off.  i cant remember.
- **Trigger**: After 2 turns when debuff expires
- **Message**: `"{unit}'s Lunacy wears off"`
- **Type**: MessageType.ABILITY
- **Proposed**: `"{unit}'s vision clears as the lunacy fades"`

**Silent Mechanic - Damage Halving** (units.py:683-693) <--remove this messaging
- **Current**: Only debug logger, no message_log
- **Purpose**: POTPOURRIST receives half damage from debuffed attackers
- **Proposed**: `"{attacker} struggles to focus on {defender}!"` (MessageType.ABILITY)

**Rationale**:
- "Demilune" = half-moon = crescent shape
- "Lunacy" = moon-madness (luna = moon)
- Debuff causes disorientation affecting combat effectiveness
- Crescent/arc language ties visual to mechanical effect

---

### **4. GRANITE GEAS (Active Skill 3 - Binding Strike with Compulsion)**

**Purpose**: Single target attack that applies geas binding (if target doesn't respond to POTPOURRIST next turn, POTPOURRIST heals 4 HP)

#### Current Messages (NEEDS REVISION - uses incorrect "gavel" language)

**Queue** (potpourrist.py:534-540)
- **Current**: `"{unit} prepares to bring down the granite gavel on {target}"`
- **ISSUE**: Skill is "Granite Geas" not "Granite Gavel"
- **RECOMMENDED**: `"{unit} readies to bind {target} with granite and oils"`

**Execute** (potpourrist.py:563-567)
- **Current**: `"{unit} brings down the granite gavel!"`
- **ISSUE**: Wrong tool imagery (gavel = judgment, geas = compulsion)
- **RECOMMENDED**: `"{unit} comes down hard on {target} with a ton of oiled granite"`

**Damage** (potpourrist.py:610-614)
- **Current**: `"{target} takes #DAMAGE_{actual_damage}# damage from Granite Geas"`
- **Proposed**: Keep as-is (standard format)

**Status Applied** (potpourrist.py:637-641)
- **Current**: `"{target} is marked by potpourri oils!"`
- **ISSUE**: Doesn't explain the compulsion mechanic
- **RECOMMENDED**: `"{target} is bound by a redolent geis"`

**Status Immunity** (potpourrist.py:643-647)
- **Current**: `"{target} is immune to Taunt due to Stasiality"`
- **ISSUE**: Uses technical term "Taunt" instead of thematic "geas"
- **RECOMMENDED**: `"{target} is immune to the geis due to stasiality"`

#### Taunt Resolution Messages (End of Turn)

**Taunt Heal - Ignored** (engine.py:3475-3479)
- **Trigger**: End of taunted unit's turn if they didn't attack/skill POTPOURRIST
- **Current**: `"{taunter} heals {actual_heal} HP from ignored taunt"`
- **ISSUE**: Uses technical term "taunt"
- **RECOMMENDED**: `"{taunter} inhales the fumes of the broken geas and restores ({actual_heal} HP)"`

**Taunt Responded** (engine.py:3490-3494) <--don't need this
- **Trigger**: When taunted unit attacked/skilled POTPOURRIST
- **Current**: `"{unit}'s taunt ends (responded)"`
- **ISSUE**: Technical language, no thematic flavor
- **RECOMMENDED**: `"{unit} honors the binding - the geas dissolves"`

**Taunt Expired** (engine.py:3496-3500) <--don't need this
- **Trigger**: When taunt duration reaches 0
- **Current**: `"{unit}'s taunt wears off"`
- **ISSUE**: Generic status expiration
- **RECOMMENDED**: `"The geas marking {unit} dissipates"`

**Rationale**:
- **Geas** = magical compulsion/oath from Celtic mythology, NOT a judgment tool
- Granite pedestal is a **conduit** for the binding, not a gavel
- Potpourri oils create the **visible mark** of the binding
- When ignored, the geas is **violated/broken**, empowering the caster (tank feeding on defiance)
- When answered, the geas is **honored/fulfilled**, releasing the target
- Language emphasizes **obligation, binding, compulsion** rather than judgment

---

## Missing/Silent Mechanics

### 1. **Demilune Damage Halving** (SILENT) <--don't need this
- **Location**: units.py:683-693 (hp setter)
- **Current**: Only debug logger
- **Recommendation**: `"{attacker} struggles to focus on {defender}!"` when debuffed attacker tries to hit POTPOURRIST

### 2. **Potpourri Consumption** (SILENT)
- **Location**: Skills consume potpourri when enhanced
- **Current**: No explicit message
- **Recommendation**: `"{unit} infuses {skill} with his potpourri blend"` when enhancement is used

---

## Message Flow Examples

### Example 1: Enhanced Demilune Combo
1. Turn start: `"α inhales restorative aromatics (2 HP)"` (has potpourri)
2. Queue: `"α hoists the granite pedestal overhead"`
3. Execute: `"α sweeps the pedestal in a crescent arc!"`
4. Hit 1: `"β takes 4 damage from Demilune"` (enhanced damage)
5. Status 1: `"β staggers under the demilune's weight!"`
6. Hit 2: `"γ takes 4 damage from Demilune"`
7. Status 2: `"γ staggers under the demilune's weight!"`
8. Later: `"β's vision clears as the lunacy fades"` (after 2 turns)

### Example 2: Granite Geas Ignored
1. Queue: `"α readies to bind β with granite and oils"`
2. Execute: `"α strikes β - the geas is sealed!"`
3. Damage: `"β takes 4 damage from Granite Geas"`
4. Status: `"β is bound by potpourri oils - the geas compels!"`
5. Next turn: β does nothing or attacks someone else
6. Heal: `"α is empowered by the violated geas (4 HP)"`
7. Expire: `"The geas marking β dissipates"`

### Example 3: Granite Geas Honored
1. Status: `"β is bound by potpourri oils - the geas compels!"`
2. Next turn: β attacks α (the POTPOURRIST)
3. Response: `"β honors the binding - the geas dissolves"`

---

## Implementation Priority

### HIGH PRIORITY - Granite Geas Corrections (Incorrect Terminology)
1. **Line 534-540**: Queue message - remove "gavel", add geas binding language
2. **Line 563-567**: Execute message - replace gavel with geas sealing
3. **Line 637-641**: Status applied - emphasize compulsion mechanic
4. **Line 643-647**: Immunity message - use "geas" not "taunt"
5. **engine.py:3475-3479**: Heal message - "violated geas" empowerment
6. **engine.py:3490-3494**: Responded message - "honors the binding"
7. **engine.py:3496-3500**: Expired message - "geas dissipates"

### MEDIUM PRIORITY - Thematic Improvements
8. Melange Eminence: "inhales restorative aromatics"
9. Demilune Status: "staggers under the demilune's weight"
10. Demilune Expire: "vision clears as the lunacy fades"

### LOW PRIORITY - Polish
11. Infuse messages: Enhanced blend creation narrative
12. Demilune swing/miss: Crescent arc consistency
13. Damage halving visibility: Make silent mechanic visible

---

## Message Type Usage

All messages follow established patterns:
- ✅ MessageType.ABILITY - skill activations, status effects, healing
- ✅ MessageType.COMBAT - damage dealt (with #DAMAGE_# format)
- ✅ MessageType.WARNING - skill missed/wasted
- ✅ Consistent with other unit skill message patterns

---

## Files to Modify

1. **boneglaive/game/skills/potpourrist.py**
   - Lines 83-87, 132-136, 146-150, 180-184 (Melange + Infuse)
   - Lines 287-291, 358-362, 409-413, 439-443, 445-449, 453-458 (Demilune)
   - Lines 534-540, 563-567, 610-614, 637-641, 643-647 (Granite Geas)

2. **boneglaive/game/engine.py**
   - Lines 3475-3479, 3490-3494, 3496-3500 (Taunt resolution)
   - Lines 3525-3529 (Lunacy expiration)

3. **boneglaive/game/units.py** (Optional)
   - Lines 683-693 (Add damage halving message)
