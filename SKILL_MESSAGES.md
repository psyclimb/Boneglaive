# Boneglaive Skill Messages

This document lists all messages displayed in the message log related to skill usage, organized by unit type and skill. Messages are shown in the order they appear during gameplay.

## GLAIVEMAN

### Autoclave (Passive)
- `"GLAIVEMAN Alpha's Autoclave activates!"`
- `"GLAIVEMAN Alpha absorbs life essence, healing for X HP!"`
- Combat messages for each enemy hit: `"GLAIVEMAN Alpha's Autoclave deals X damage to GRAYMAN Beta!"`
- For defeated enemies: `"GRAYMAN Beta perishes!"`

### Pry
- **When readied**: `"GLAIVEMAN Alpha readies to launch GRAYMAN Beta skyward!"`
- **When executed**: 
  - Close range: `"GLAIVEMAN Alpha pries GRAYMAN Beta upward with their glaive!"`
  - Longer range: `"GLAIVEMAN Alpha launches GRAYMAN Beta skyward with their glaive!"`
  - If target becomes invalid: `"Pry failed: target no longer valid."`
- **Combat message**: `"GLAIVEMAN Alpha's Pry deals X damage to GRAYMAN Beta!"`
- **Splash damage**: `"GLAIVEMAN Alpha's Pry Debris deals X damage to GRAYMAN Gamma!"`
- **Movement penalty**: `"GRAYMAN Beta's movement reduced by 1 for next turn!"`
- **Stasiality immunity**: `"GRAYMAN Beta is immune to Pry's movement penalty due to Stasiality!"`
- **When target defeated**: `"GRAYMAN Beta perishes!"`
- **When splash target defeated**: `"GRAYMAN Gamma perishes from falling debris!"`

### Vault
- **When readied**: `"GLAIVEMAN Alpha prepares to vault to position (X, Y)!"`
- **When executed**: 
  - Start: `"GLAIVEMAN Alpha prepares to vault!"`
  - Completion: `"GLAIVEMAN Alpha vaults to position (X, Y)!"`

### Judgement
- **When readied**: `"GLAIVEMAN Alpha readies a sacred glaive to throw at GRAYMAN Beta!"`
- **When executed**: 
  - Start: `"GLAIVEMAN Alpha hurls a sacred glaive!"`
  - Effect: `"The sacred glaive bypasses GRAYMAN Beta's defenses!"`
  - Critical effect: `"The sacred glaive strikes with divine judgement!"`
- **Combat message**: `"GLAIVEMAN Alpha's Judgement deals X damage to GRAYMAN Beta!"`
- **When target defeated**: `"GRAYMAN Beta perishes!"`

## GRAYMAN

### Stasiality (Passive)
- No specific messages (passive immunity)
- Immunity messages appear in other skills when targeting a GRAYMAN with Stasiality

### Delta Config
- **When readied**: `"GRAYMAN Alpha prepares to shift to Delta Config (X, Y)!"`
- **When executed**:
  - Start: `"GRAYMAN Alpha initiates Delta Config!"`
  - Completion: `"GRAYMAN Alpha teleports to position (X, Y)!"`

### Estrange
- **When readied**: `"GRAYMAN Alpha charges the estrangement beam targeting MANDIBLE_FOREMAN Beta!"`
- **When executed**: `"GRAYMAN Alpha fires an estrangement beam at MANDIBLE_FOREMAN Beta!"`
- **Combat message**: `"GRAYMAN Alpha's Estrange deals X damage to MANDIBLE_FOREMAN Beta!"`
- **Status effect**: `"MANDIBLE_FOREMAN Beta is phased out of normal spacetime!"`
- **Stasiality immunity**: `"MANDIBLE_FOREMAN Beta is immune to Estrange due to Stasiality!"`
- **When target defeated**: `"MANDIBLE_FOREMAN Beta perishes!"`

### Græ Exchange
- **When readied**: `"GRAYMAN Alpha initiates the Græ Exchange ritual targeting position (X, Y)!"`
- **When executed**:
  - Start: `"GRAYMAN Alpha begins the Græ Exchange ritual!"`
  - Completion: `"GRAYMAN Alpha creates an echo and teleports to (X, Y)!"`

## MANDIBLE_FOREMAN

### Viseroy (Passive)
- No specific messages (passive trapping effect)
- Messages appear when targets are trapped (see below)

### Expedite (formerly Discharge)
- **When readied**: `"MANDIBLE_FOREMAN Alpha readies to expedite to position (X, Y)!"`
- **When executed**: `"MANDIBLE_FOREMAN Alpha expedites forward!"`
- **Combat message** (if enemy hit): `"MANDIBLE_FOREMAN Alpha's Expedite deals X damage to GRAYMAN Beta!"`
- **Trapping effect**: `"GRAYMAN Beta is trapped in MANDIBLE_FOREMAN Alpha's mechanical jaws!"`
- **Stasiality immunity**: `"GRAYMAN Beta is immune to Expedite's trapping effect due to Stasiality!"`
- **When target defeated**: `"GRAYMAN Beta perishes!"`

### Site Inspection
- **When readied**: `"MANDIBLE_FOREMAN Alpha prepares to inspect the site around (X, Y)!"`
- **When executed**:
  - Start: `"MANDIBLE_FOREMAN Alpha begins inspecting the site around (X, Y)!"`
  - Completion: `"MANDIBLE_FOREMAN Alpha completes site inspection. All allies in the area gain +1 to attack and movement!"`

### Jawline
- **When readied**: `"MANDIBLE_FOREMAN Alpha prepares to deploy a JAWLINE network!"`
- **When executed**: `"MANDIBLE_FOREMAN Alpha deploys JAWLINE network!"`
- **Combat message** (for each enemy hit): `"MANDIBLE_FOREMAN Alpha's Jawline deals X damage to GRAYMAN Beta!"`
- **Status effect**: `"GRAYMAN Beta's movement is reduced by the Jawline tether!"`
- **Stasiality immunity**: `"GRAYMAN Beta is immune to Jawline's movement penalty due to Stasiality!"`
- **When target defeated**: `"GRAYMAN Beta perishes!"`

## MARROW_CONDENSER

### Dominion (Passive)
- **When enemy dies in Marrow Dike**: `"MARROW_CONDENSER Alpha absorbs power from the fallen, upgrading X!"`

### Ossify
- **When readied**: `"MARROW_CONDENSER Alpha prepares to ossify their bones!"`
- **When executed (normal)**: `"MARROW_CONDENSER Alpha's bones harden, increasing defense by X but reducing mobility!"`
- **When executed (upgraded)**: `"MARROW_CONDENSER Alpha's bones permanently harden, increasing defense by X!"`

### Marrow Dike
- **When readied**: `"MARROW_CONDENSER Alpha prepares to create a Marrow Dike!"`
- **When executed (normal)**: `"MARROW_CONDENSER Alpha creates a Marrow Dike!"`
- **When executed (upgraded)**: `"MARROW_CONDENSER Alpha creates a reinforced Marrow Dike with stronger walls!"`
- **When walls expire**: `"A section of MARROW_CONDENSER Alpha's Marrow Dike crumbles away..."`

### Slough
- **When readied**: `"MARROW_CONDENSER Alpha prepares to transfer bonuses to GLAIVEMAN Beta!"`
- **When executed (normal)**: `"MARROW_CONDENSER Alpha transfers their stat bonuses to GLAIVEMAN Beta!"`
- **When executed (upgraded)**: `"MARROW_CONDENSER Alpha shares their stat bonuses with GLAIVEMAN Beta without losing them!"`
- **When transfer fails**: `"Slough failed: target no longer valid."`

## General Message Format Patterns

1. **Skill Readying**: "UnitName prepares/readies to use SkillName on target!"
2. **Skill Execution Start**: "UnitName begins using SkillName!"
3. **Combat Messages**: "UnitName's SkillName deals X damage to TargetName!"
4. **Status Effect Application**: "TargetName is affected by status effect!"
5. **Immunity Messages**: "TargetName is immune to SkillName's effects due to Stasiality!"
6. **Unit Defeat**: "TargetName perishes!"
7. **Skill Completion**: "UnitName completes SkillName with resulting effect!"

## Message Types

Messages use different MessageType values for proper coloring in the log:
- `MessageType.ABILITY` for skill activation and effects
- `MessageType.COMBAT` for damage dealing and unit defeat