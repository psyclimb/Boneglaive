# Imbued Furniture Animation - Implementation Complete

## Summary
Created persistent animation for furniture imbued by Market Futures, displaying a glowing ¤ currency symbol with continuous gold sparkle stream.

## Visual Features

### Currency Symbol (¤)
- **Character:** ¤ (generic currency symbol)
- **Color:** Gold (255, 215, 0)
- **Alpha:** Pulsing 120-200 (semi-transparent)
- **Size:** 40pt font with pulsing scale (0.9x - 1.1x)
- **Position:** Centered on imbued furniture tile
- **Effect:** Gentle oscillation synchronized with astral value pulse
- **Outline:** Black semi-transparent outline for visibility

### Gold Sparkles
- **Spawn Rate:** 2-3 sparkles per frame (120-180 per second at 60fps)
- **Colors:** Bright gold (255, 235, 100) and gold (255, 215, 0) alternating
- **Size:** 2-4px circles
- **Lifetime:** 1.0-1.5 seconds
- **Motion:** 
  - Upward velocity: -40 to -60 px/s (negative = up)
  - Horizontal drift: -10 to +10 px/s
- **Spawn Area:** Random within central ⅓ of tile
- **Fade:** Alpha 220 → 0 over lifetime

## Implementation Details

### File Modified
**boneglaive/graphical/renderer.py**

**Changes:**
1. Line 123: Added `self.imbued_sparkles = []` to `__init__`
2. Lines 899-915: Added sparkle update logic in `update()` method
3. Lines 1782-1874: Added `draw_imbued_furniture()` method
4. Line 1493: Hooked drawing into main `draw()` loop

### Persistence Logic
```python
# Automatically checks game.teleport_anchors for imbued furniture
for anchor_pos, anchor_data in game.teleport_anchors.items():
    if anchor_data.get('imbued', False):
        # Draw currency symbol and spawn sparkles
```

### Sparkle Data Structure
Each sparkle is a lightweight dict:
```python
{
    'x': float,           # Screen X position
    'y': float,           # Screen Y position
    'vx': float,          # Horizontal velocity
    'vy': float,          # Vertical velocity (negative = up)
    'life': float,        # Current age in seconds
    'max_life': float,    # Total lifetime in seconds
    'size': int,          # Radius in pixels (2-4)
    'color': tuple        # RGB color
}
```

## Behavior

### Activation
- Automatically appears when Market Futures is cast on furniture
- No manual activation needed - checks `'imbued': True` flag

### Deactivation
- Automatically disappears when furniture is no longer imbued
- Occurs when:
  - Ally uses the teleport anchor
  - Game sets `'imbued': False`
- Sparkles fade out naturally over 1-1.5 seconds

### Performance
- Lightweight system (not full Particle objects)
- Sparkles cleaned up automatically when lifetime expires
- Only processes imbued furniture (typically 0-3 at a time)
- No impact on game logic or animation system

## Testing Instructions

### Setup
1. Run graphical version: `python run_graphical.py`
2. Select DELPHIC APPRAISER unit
3. Have furniture pieces available in range

### Test Procedure
1. Press 'M' to activate Market Futures skill
2. Target a furniture piece within range 4
3. Cast the skill (animation plays)
4. **Observe imbued furniture:**
   - [ ] Pulsing gold ¤ symbol appears centered on furniture
   - [ ] Symbol oscillates smoothly (0.9x-1.1x scale, 120-200 alpha)
   - [ ] Gold sparkles continuously stream upward from tile
   - [ ] Sparkles have slight horizontal drift
   - [ ] Sparkles fade as they rise
   - [ ] 2-3 new sparkles spawn per frame
5. Move an ally adjacent to the imbued furniture
6. Activate teleport by clicking destination
7. **Verify cleanup:**
   - [ ] ¤ symbol disappears immediately
   - [ ] Existing sparkles fade out naturally
   - [ ] No new sparkles spawn

### Expected Visual
- Beautiful, wispy gold particle stream rising from furniture
- Clear ¤ indicator showing which furniture has active Market Futures
- Smooth, continuous animation that doesn't interfere with gameplay
- Automatic cleanup when anchor is used

## Integration Status
✅ Sparkle list added to renderer
✅ Update logic implemented
✅ Drawing method created
✅ Hooked into main draw loop
✅ Syntax verified
✅ Ready for testing

## Technical Notes
- Uses same pulse timer as astral values for consistency
- Draws after astral values but before units (correct layer)
- No dependencies on animation_factory or active_animations
- Independent of skill animation system
- Automatically handles multiple imbued furniture simultaneously

This creates a clear, beautiful visual indicator that Market Futures is active on furniture!
