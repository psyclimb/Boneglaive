# FOWL CONTRIVANCE Universal Rail Bomb System

## Overview
The FOWL CONTRIVANCE rail system has been completely redesigned with a **Universal Rail Bomb** platform - a single explosive ordnance design that supports movement in all cardinal directions from any tile.

## Design Philosophy

### Previous System (REPLACED)
- Three separate graphics: `rail_ns.svg`, `rail_ew.svg`, `rail_cross.svg`
- Required smart detection logic to determine which variant to use
- Traditional railroad track aesthetic

### New System (CURRENT)
- **One universal design**: `rail_universal.svg`
- Explosive ordnance/bomb platform aesthetic
- Simplified rendering - no variant detection needed
- Every rail tile supports all cardinal directions (N, S, E, W)

## Visual Design Features

The Universal Rail Bomb includes:

1. **Explosive Core**
   - Glowing orange/yellow energy center
   - Radiating pulse rings
   - Hazard symbol in center

2. **Military/Industrial Aesthetic**
   - Metallic shell casing with rivets
   - Missile-like stabilizer fins (4 cardinal directions)
   - Warning stripes (yellow/black hazard markings)
   - Explosive blast scoring/burn marks

3. **Rail Extensions**
   - Steel rails extending in all 4 cardinal directions (N, S, E, W)
   - Metallic shine highlights
   - Connection bolts at rail junctions

4. **Semi-Transparent Overlay**
   - ~85% opacity allows underlying terrain to show through
   - Rails don't replace terrain - they overlay on top

## Implementation

### Files Created/Modified

**New Graphics:**
- `graphics/terrain/rail_universal.svg` - Universal rail bomb platform (5.7 KB)

**Code Changes:**
- `boneglaive/graphical/renderer.py`:
  - Modified `_load_rail_overlays()` to load single universal rail
  - Simplified `draw_grid()` Pass 2 to use universal rail for all tiles
  - Changed from `rail_overlays` dict to single `rail_universal` surface

**Map System:**
- `boneglaive/game/map.py`:
  - Added `get_rail_type()` method (kept for reference, not used by universal system)
  - Existing rail generation and management unchanged

### Rendering Process

**Two-Pass Rendering:**
1. **Pass 1**: Draw base terrain (using original terrain stored before rails)
2. **Pass 2**: Overlay universal rail bomb on all rail tiles

```python
# Pass 2 is now ultra-simple
if terrain_type == TerrainType.RAIL:
    surface.blit(self.rail_universal, (tile_x, tile_y))
```

## Gameplay Integration

### How It Works
- First FOWL CONTRIVANCE spawned generates the rail network
- Rails are placed on passable terrain only
- Each rail tile becomes a Universal Rail Bomb platform
- FOWL CONTRIVANCE units can move in any cardinal direction from any rail
- When any FOWL dies: rails explode for 4 damage to enemies standing on them
- When last FOWL dies: entire network is removed

### Network Layout
The rail network creates 66 bomb platforms in a strategic pattern:
- Horizontal line at row 3 (20 tiles wide)
- Vertical lines at columns 8 & 12 (10 tiles tall each)
- Corner connections along rows 1 and 8
- Strategic flanking positions

## Testing

Run the test script to verify the system:
```bash
python test_universal_rail.py
```

Expected output:
- 66 rail bomb platforms placed
- Visual map showing bomb network with 'X' markers
- Sample platforms showing all cardinal movement enabled
- System features checklist

## Advantages Over Previous System

1. **Simplicity**: One graphic instead of three
2. **No Detection Logic**: No need to check adjacent tiles
3. **Thematic Consistency**: Explosive aesthetic matches FOWL's rail cannon weapon
4. **Universal Movement**: Every tile explicitly supports all directions
5. **Visual Impact**: More dramatic and militaristic appearance
6. **Performance**: Simpler rendering logic

## Future Considerations

The universal rail bomb design could be enhanced with:
- Animated glowing core (pulsing energy)
- Different colored explosives for different teams
- Damage indicators when rails explode
- Particle effects on rail placement (from rail cannon)

## Files Reference

**Graphics (Active):**
- `/home/user/boneglaive/graphics/terrain/rail_universal.svg` - Universal rail bomb (ONLY rail graphic used)

**Graphics (Archived):**
- `/home/user/boneglaive/graphics/terrain/archive_old_rails/rail.svg` - Original NS-only rail (deprecated)
- `/home/user/boneglaive/graphics/terrain/archive_old_rails/rail_ns.svg` - Vertical variant (deprecated)
- `/home/user/boneglaive/graphics/terrain/archive_old_rails/rail_ew.svg` - Horizontal variant (deprecated)
- `/home/user/boneglaive/graphics/terrain/archive_old_rails/rail_cross.svg` - Junction variant (deprecated)

**Code:**
- `/home/user/boneglaive/boneglaive/graphical/renderer.py`:
  - Line 187: Removed RAIL from terrain_svg_map (now overlay-only)
  - Lines 147-149: Universal rail surface initialization
  - Lines 256-283: Universal rail loader
  - Lines 1967-1979: Two-pass rendering with universal rail overlay
- `/home/user/boneglaive/boneglaive/game/map.py` (lines 340-374): Rail type detection (kept for reference)

**Tests:**
- `/home/user/boneglaive/test_universal_rail.py` - Universal rail bomb system test
- `/home/user/boneglaive/test_rail_graphics.py` - Original variant detection test (deprecated)

---

**Status**: ✅ IMPLEMENTED AND TESTED
**Date**: 2025-12-04
**Version**: Graphical Mode Only
