# POTPOURRIST - Tank Unit Design Document

## Concept
- **Role**: Tank with high HP pool and health regeneration
- **Visual**: Big burly guy in a flowered pattern shirt wielding a granite pedestal
- **Theme**: Potpourri-based healing and empowerment

## Base Stats
- **HP**: 28 (highest in game - current max is 22)
- **Attack**: 4 (standard)
- **Defense**: 0 (tankiness from HP pool, not armor)
- **Move range**: 2
- **Attack range**: 1 (melee)

## Visual Representation
- **Symbol**: P
- **Attack effect**: I (pedestal strike)

---

## Skills

### Passive: Melange Eminence
**Description**: Heals 1 HP every turn. This effect cannot be prevented by any effect (bypasses Auction Curse and similar healing prevention).

**Mechanics**:
- Triggers at the start of each turn
- Bypasses all healing prevention effects
- Increases to 3 HP/turn while holding potpourri from Commingle

---

### Active Skill 1: Commingle
**Key**: [TBD]

**Description**: Creates a potpourri mix that enhances the next skill.

**Mechanics**:
- Targets self (automatic, no targeting required)
- Creates potpourri that is held by POTPOURRIST
- While holding potpourri:
  - Melange Eminence heals +2 HP (total 3 HP/turn instead of 1)
  - Next active skill used receives enhancement bonus
- Potpourri is consumed when the next skill is used
- Enhancement effects are specific to each skill (see below)
- Can only be used when NOT already holding potpourri

**Range**: Self
**Cooldown**: 0 (but limited by potpourri_held flag)

---

### Active Skill 2: Demilune
**Key**: [TBD]

**Description**: Swings the granite pedestal in a forward arc, dealing damage and weakening enemies against the POTPOURRIST.

**Area of Effect** (5 adjacent tiles):
```
X X X
X P X
```

**Damage**:
- Base: 3
- Enhanced: 4

**Status Effect Applied**:
- Base: Affected units deal half damage to POTPOURRIST (all damage sources)
- Enhanced: Damage halved + affected units also have their defense halved when attacked by POTPOURRIST
- Duration: 2 turns

**Cooldown**: 2 turns

**Mechanics**:
- Hits all enemy units in the forward arc (enemies only, not allies)
- Status effect is POTPOURRIST-specific (only affects interactions with the POTPOURRIST)
- Enhanced version increases both damage output and provides defensive penetration

---

### Active Skill 3: Granite Gavel
**Key**: [TBD]

**Description**: Brings down the granite pedestal like a judge's gavel. The impact releases potpourri fragments that mark the target, compelling them to respond.

**Range**: 3

**Damage**: 4

**Status Effect Applied**:
- Taunt: If the target doesn't attack or use a skill on POTPOURRIST on their next turn, POTPOURRIST heals 4 HP at the end of that turn
- Duration: 1 turn (resolved on target's next turn)

**Enhanced Effect**:
- Taunt duration increased to 2 turns
- POTPOURRIST can heal 4 HP at the end of each turn the target doesn't attack/skill them
- Taunt expires after 2 turns or when target attacks/skills POTPOURRIST

**Cooldown**: 2 turns

**Mechanics**:
- Single target attack
- At the end of taunted unit's turn, check if they attacked/skilled POTPOURRIST
- If not, POTPOURRIST heals 4 HP
- Base: Taunt expires after 1 turn
- Enhanced: Taunt lasts 2 turns, can heal POTPOURRIST each turn (up to 8 HP total if never responded to)
- Taunt ends early if target attacks/skills POTPOURRIST
- No forced targeting - target is free to act normally but incentivized to attack POTPOURRIST

---

## Gameplay Strategy

### Strengths
- Highest HP pool in the game (28 HP)
- Consistent self-healing every turn
- Can force enemies to engage with taunt
- Area denial with Demilune debuffs
- Enhanced skills provide significant tactical advantages

### Weaknesses
- No defense stat (relies on HP pool)
- Low mobility (move range 2)
- Melee range only (range 1 basic attack)
- Requires setup with Commingle for maximum effectiveness
- Cooldown management required for optimal play

### Playstyle
1. Use Commingle to create potpourri
2. Engage with enhanced Demilune for area control
3. Use Granite Gavel to force key targets to attack you
4. Tank damage with high HP pool and consistent regeneration
5. Time enhancements strategically based on battlefield needs

---

## Implementation Notes

### New Status Effects Needed
1. **Demilune Debuff**: Custom effect that halves ALL damage dealt to POTPOURRIST (intercepted in hp setter)
2. **Granite Gavel Taunt**: Track if target attacked/skilled POTPOURRIST during their turn; heal POTPOURRIST if they didn't
3. **Potpourri Held**: Buff state that enhances Melange Eminence and marks next skill for enhancement

### Special Mechanics
- Melange Eminence must bypass ALL healing prevention (special flag needed)
- Potpourri enhancement system requires tracking which skill consumes it
- Granite Gavel taunt: Track taunted unit's actions during their turn, resolve at turn end
- Demilune damage halving: Store `game.current_attacker` during damage dealing, check in hp setter (units.py:580) after PRT
- Commingle: Self-targeting skill with cooldown 0, gated by `potpourri_held` flag (can't use if already holding)

### Balance Considerations
- 28 HP + 1 HP regen = very durable tank
- Consider whether Demilune should affect allies or only enemies
- Enhancement timing creates interesting decision-making
