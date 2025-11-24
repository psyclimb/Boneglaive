# Divine Depreciation Visual Enhancement

## Change Summary
Expanded the shockwave ring radius in Divine Depreciation animation to visually cover the full 7×7 affected area.

## Problem
- Divine Depreciation affects a 7×7 tile area (radius of 3.5 tiles from center)
- Brown concentric shockwave rings only expanded to 150px radius
- This only covered ~4.7 tiles, leaving edge tiles without clear visual feedback
- Visual effect didn't match the mechanical AoE

## Solution
- Increased ShockwaveRing maximum radius from 150px → 224px
- Calculation: 7 tiles × 64px/tile ÷ 2 = 224px radius
- Now rings expand exactly to the edges of the 7×7 affected area

## File Modified
**boneglaive/graphical/animations/delphic_appraiser.py**
- Line 180: `radius = int(progress * 224)`
- Added comment explaining the calculation

## Visual Impact
- Brown concentric rings now reach all 7×7 tiles affected by the skill
- Better visual clarity of the skill's actual AoE
- Center blackhole effect remains unchanged
- Timing and fade-out behavior preserved
- 4 staggered shockwave rings still create dramatic implosion effect

## Testing Notes
When testing Divine Depreciation:
1. Cast on furniture piece
2. Observe implosion phase (Phase 3)
3. Brown shockwave rings should now expand to cover entire 7×7 area
4. Visual coverage should match where furniture rerolls occur
5. Ring thickness (4px) and brown color (139, 69, 19) unchanged

## Technical Details
- TILE_SIZE = 64px (from core.py)
- 7×7 area = 7 tiles total
- Center to edge = 3.5 tiles = 3.5 × 64px = 224px
- 4 rings with staggered delays: 0s, 0.15s, 0.3s, 0.45s
- Duration: 0.8 seconds per ring
- Fade-out: alpha = 255 × (1.0 - progress)

✅ Change complete and verified
