# Boneglaive v0.7.2 Implementation Plan

## Overview
This document outlines the systematic implementation of 40+ changes from `boneglaive_v0.7.2_notes.md`, organized by priority and complexity.

## Phase 1: Critical System Fixes (Hardest/Most Critical)

### A. AI System Bug Fix (Critical) - PRIORITY 1
- **Issue**: VS AI mode AI stops working on "new round"
- **Root Cause**: `reset_game()` creates new Game instance but doesn't reinitialize AI controller
- **Files**: 
  - `boneglaive/ui/game_ui.py:257-291` (reset_game method)
  - `boneglaive/ai/ai_interface.py` (cleanup/reinit)
- **Solution**: Reinitialize network interface (including AI) with new game instance
- **Complexity**: High - requires deep AI state management

### B. Input System Enhancement (Critical) - PRIORITY 2
- **Issue 1**: Shift+Tab not working in TTY, not picking up shift or dual key presses
- **Issue 2**: 'q' needs concede dialog instead of instant abort
- **Files**: 
  - `boneglaive/utils/input_handler.py:100+` (key mappings)
  - `boneglaive/ui/game_ui.py` (handle_input method)
  - `boneglaive/ui/ui_components.py` (new concede dialog)
- **Solution**: Fix terminal input detection, create concede dialog similar to GameOverPrompt
- **Complexity**: High - terminal input handling and new dialog system

### C. Unit Selection Bug Fix (Critical) - PRIORITY 3
- **Issue**: Cannot select units after issuing Marrow Condenser skills, only tab works
- **Files**: 
  - `boneglaive/game/skills/marrow_condenser.py`
  - `boneglaive/ui/game_ui.py` (selection state management)
- **Solution**: Investigate UI state after skill usage, ensure selection mode is restored
- **Complexity**: High - UI state management after skill usage

## Phase 2: Status Effect System (Hard)

### A. Gas Machinist Vapor System Overhaul - PRIORITY 4
- **Greek Letter Naming**: Add α,β,γ,δ identifiers to all vapors in UI and logs
- **Vapor Cleanup**: Remove all vapors when owner dies
- **Untargetable Status**: Convert Saft-E-Gas effect to proper status effect with icon
- **Files**: 
  - `boneglaive/game/skills/gas_machinist.py` (all vapor skills)
  - `boneglaive/game/engine.py` (handle_unit_death method)
  - `boneglaive/game/units.py` (status effect properties)
- **Complexity**: High - comprehensive system rework

### B. Market Futures Anchor System - PRIORITY 5
- **Anchor Status Effect**: Add visual status indicator for teleport ability
- **Access Control**: Prevent enemy anchor usage
- **Files**: 
  - `boneglaive/game/skills/delphic_appraiser.py:97+` (MarketFuturesSkill)
- **Solution**: Add "Anchor" status effect with icon, check ownership in teleport logic
- **Complexity**: Medium-High - new status effect system

## Phase 3: Animation & Visual Feedback (Medium)

### A. Animation Improvements - PRIORITY 6
- **Judgement**: Fix black tile animation artifacts (`boneglaive/game/skills/glaiveman.py`)
- **Estrange**: Replace beam symbols for basic terminals (`boneglaive/game/skills/grayman.py`)
- **Divine Depreciation**: Delay damage display until after animation (`boneglaive/game/skills/delphic_appraiser.py`)
- **Files**: Multiple skill files, `boneglaive/utils/asset_manager.py`
- **Complexity**: Medium - animation timing and visual assets

### B. Map Visual Updates - PRIORITY 7
- **Stained Stones**: Color matching with help text (`boneglaive/game/map.py`)
- **Rails**: Gray with black background (not red) (`boneglaive/renderers/curses_renderer.py`)
- **Files**: `boneglaive/game/map.py`, `boneglaive/renderers/curses_renderer.py`
- **Complexity**: Medium - color scheme changes

## Phase 4: Message System Refinement (Medium-Low)

### A. Message Content & Styling - PRIORITY 8
- **"Retches" Messages**: Red text formatting (partially implemented at `boneglaive/utils/message_log.py:245`)
- **Fragcrest Messages**: 
  - Yellow shrapnel text: "Shrapnel is embedded deeply in [unit]"
  - Remove exclamation points from damage messages
  - Remove extraneous pierce/fragmentation messages
- **Gas Machinist**: 
  - Yellow damage numbers for CUTTING GAS
  - Remove exclamation points from all messages
- **Divine Depreciation**: 
  - Cosmic value re-roll messages: "[furniture]'s cosmic value has been re-rolled to [value]"
  - Collision damage: "[unit] slams into the [furniture] for 1 damage" (yellow damage)
- **Files**: `boneglaive/utils/message_log.py`, individual skill files
- **Complexity**: Low-Medium - text formatting and message cleanup

### B. Message Log Cleanup - PRIORITY 9
- **Remove**: "You can only use skills with your own units" from log (not UI)
- **Remove**: Extraneous Fragcrest messages: "The projectile pierces X target for 10 damage"
- **Remove**: "Fragmentation hits X units for Y damage and embeds shrapnel"
- **Files**: `boneglaive/ui/game_ui.py`, `boneglaive/game/skills/fowl_contrivance.py`
- **Complexity**: Low - message filtering

## Phase 5: Content & Polish (Low)

### A. Content Updates - PRIORITY 10
- **Terminology**: "Dec Table" → "End Table"
  - `boneglaive/game/map.py:23` (TerrainType.DEC_TABLE)
  - `boneglaive/utils/asset_manager.py:66` ('dec_table' key)
  - `boneglaive/game/skills/delphic_appraiser.py:662` (display name)
- **Interferer**: [C]arrier Rave → [K]arrier Rave + keybind change
  - `boneglaive/game/skills/interferer.py` (skill key and name)
- **Help File**: 
  - Add plutonium tipped carbiner description to Interferer
  - Remove "Radio warfare specialist" from roles
  - Remove "(Radioactive interference)" and "Plutonium carabiner cross)" references
- **Complexity**: Low - text and identifier changes

### B. Minor Features - PRIORITY 11
- **Marrow Condenser**: Ground indicator for move commands
- **Fragcrest**: Displacement coordinate messages like Divine Depreciation
- **Files**: 
  - `boneglaive/game/skills/marrow_condenser.py`
  - `boneglaive/game/skills/fowl_contrivance.py`
- **Complexity**: Low - minor feature additions

## Detailed Change Tracking

### General (4 items)
1. ✅ AI not acting on new round - Phase 1A
2. ✅ 'q' concede dialog - Phase 1B  
3. ✅ "retches" red text - Phase 4A
4. ✅ Dec table → End table - Phase 5A

### Map Changes (1 item)
5. ✅ Stained stones color - Phase 3B

### Unit-Specific Changes:

#### GLAIVEMAN (1 item)
6. ✅ Judgement animation fix - Phase 3A

#### GRAYMAN (1 item) 
7. ✅ Estrange beam animation - Phase 3A

#### MARROW CONDENSER (2 items)
8. ✅ Ground indicator for moves - Phase 5B
9. ✅ Unit selection bug - Phase 1C

#### FOWL CONTRIVANCE (5 items)
10. ✅ Rails gray/black - Phase 3B
11. ✅ Fragcrest displacement coords - Phase 5B
12. ✅ Yellow shrapnel message - Phase 4A
13. ✅ Yellow damage, no '!' - Phase 4A
14. ✅ Remove pierce message - Phase 4B
15. ✅ Remove fragmentation message - Phase 4B

#### GAS MACHINIST (5 items)
16. ✅ Remove vapors on death - Phase 2A
17. ✅ Greek letter naming - Phase 2A
18. ✅ CUTTING GAS yellow damage - Phase 4A
19. ✅ Remove exclamation points - Phase 4A
20. ✅ Saft-E-Gas status effect - Phase 2A

#### DELPHIC APPRAISER (6 items)
21. ✅ Market Futures anchor status - Phase 2B
22. ✅ Divine Depreciation re-roll messages - Phase 4A
23. ✅ Enemy anchor access prevention - Phase 2B
24. ✅ Divine Depreciation damage delay - Phase 3A
25. ✅ Terrain collision damage - Phase 4A

#### INTERFERER (4 items)
26. ✅ Carrier → Karrier Rave - Phase 5A
27. ✅ Help page plutonium mention - Phase 5A
28. ✅ Remove "Radio warfare specialist" - Phase 5A
29. ✅ Remove radioactive references - Phase 5A

### Input System (2 items)
30. ✅ Shift+Tab fix - Phase 1B
31. ✅ Remove "only own units" message - Phase 4B

## Implementation Strategy

1. **Phase 1**: Address critical bugs that break gameplay
2. **Phase 2**: Implement complex system changes requiring architectural work  
3. **Phase 3**: Polish visual and animation systems
4. **Phase 4**: Clean up and standardize messaging
5. **Phase 5**: Content updates and minor enhancements

**Estimated Total**: 31 distinct changes across 15+ files
**Risk Areas**: AI system, input handling, status effect architecture
**Testing Priority**: VS AI mode, Marrow Condenser skills, terminal input

## Current Status
- **Started**: Phase 1A (AI System Bug Fix)
- **Next**: Complete AI fix, then proceed to input system