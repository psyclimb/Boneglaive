# Camera System Implementation

## Overview
Implemented a centralized Camera system to make animations resize-safe and support future features like zoom and pan.

## Problem
Previously, coordinate conversion was hard-coded in multiple places:
- `animation_factory.py` had `GRID_OFFSET_X = 100` and `GRID_OFFSET_Y = 50`
- Each animation received pixel coordinates
- Changing grid layout would break all animations

## Solution
Created a `Camera` class that:
- Centralizes all coordinate conversion logic
- Stores grid offset and tile size
- Supports screen shake integration
- Enables future zoom/pan features

## Files Changed

### 1. `/boneglaive/graphical/camera.py` (NEW)
```python
class Camera:
    def __init__(self, grid_offset_x=100, grid_offset_y=50, tile_size=64):
        self.grid_offset_x = grid_offset_x
        self.grid_offset_y = grid_offset_y
        self.tile_size = tile_size
        self.shake_offset_x = 0
        self.shake_offset_y = 0

    def grid_to_screen(self, grid_x, grid_y, centered=True):
        """Convert grid coordinates to screen pixels."""
        # Includes shake offset automatically

    def screen_to_grid(self, screen_x, screen_y):
        """Convert screen pixels to grid coordinates."""

    def update_layout(self, grid_offset_x=None, grid_offset_y=None, tile_size=None):
        """Update layout parameters (enables resize)."""
```

### 2. `/boneglaive/graphical/renderer.py`
**Changes:**
- Added `from .camera import Camera`
- Created `self.camera = Camera(...)` in `__init__`
- Added `camera=self.camera` to all `AnimationFactory.create_animation()` calls
- Updated `draw()` to set camera shake: `self.camera.set_shake(shake_offset_x, shake_offset_y)`

### 3. `/boneglaive/graphical/animations/animation_factory.py`
**Changes:**
- Added `camera = None` parameter to `create_animation()`
- Replaced hard-coded `grid_to_screen()` function with `camera.grid_to_screen`
- Added fallback for backwards compatibility (with warning)
- Removed hard-coded `GRID_OFFSET_X` and `GRID_OFFSET_Y` constants

## Benefits

### Immediate
✅ Single source of truth for coordinate conversion
✅ Animations automatically include screen shake
✅ Easy to change grid layout (just update camera constructor)

### Future
✅ **Zoom support** - Change `camera.tile_size`
✅ **Pan support** - Change `camera.grid_offset_x/y`
✅ **Camera effects** - Smooth panning, zoom animations
✅ **Multiple viewports** - Create multiple cameras for split-screen

## Usage

### Changing Grid Layout
```python
# In renderer.__init__() or anytime:
self.camera.update_layout(grid_offset_x=150, grid_offset_y=100, tile_size=48)
# All animations will automatically use new layout!
```

### Adding Zoom
```python
# Zoom in 2x
self.camera.tile_size = 128  # Double the tile size
# Animations will automatically scale!
```

### Panning the View
```python
# Pan the camera right by 100 pixels
self.camera.grid_offset_x += 100
```

## Backwards Compatibility
- Falls back to default offsets if no camera is provided
- Prints warning: `"WARNING: No camera provided, using default offsets"`
- Existing code continues to work

## Testing
```bash
# Test camera import
python -c "from boneglaive.graphical.camera import Camera; c = Camera(); print(c.grid_to_screen(5, 5))"

# Test renderer with camera
python -c "from boneglaive.graphical.renderer import GraphicalRenderer; print('OK')"
```

## Next Steps
- **Optional:** Migrate individual animations to store grid coords instead of screen coords
- **Optional:** Add smooth camera transitions for panning/zooming
- **Optional:** Add camera following (follow selected unit)

## Notes
- Screen shake is now integrated with camera system
- All existing animations work without modification
- Future animations should use camera for any coordinate queries
