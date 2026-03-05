# Resolution Scaling System

## Overview
The Boneglaive graphical version now supports dynamic resolution scaling, allowing players to change screen resolution from the Display Settings menu. All UI elements scale proportionally to maintain playability at different resolutions.

## Supported Resolutions
- 1280x720 (720p HD)
- 1280x800 (16:10)
- 1440x900 (16:10)
- 1480x800 (Default)
- 1600x900 (HD+)
- 1680x1050 (16:10)
- 1920x1080 (Full HD)
- 2560x1440 (2K)

Note: 4K (3840x2160) is defined but excluded from the menu for stability reasons.

## Architecture

### Core Components

#### 1. Resolution System (`boneglaive/utils/resolution.py`)
- `ResolutionPresets`: Defines common resolution presets
- `LayoutConfig`: Calculates dynamic layout dimensions based on screen size
- Proportional scaling for panels, bars, and tile sizes
- Font scaling with minimum size constraints

#### 2. Display Settings Menu (`boneglaive/graphical/ui/settings_menu.py`)
- Resolution selector button (cycles through supported resolutions)
- Fullscreen toggle button
- Apply button (appears when resolution changes are pending)
- Filters resolutions based on available display modes

#### 3. Menu Manager (`boneglaive/graphical/ui/menu_manager.py`)
- Handles "change_resolution" and "toggle_fullscreen" actions
- Recreates display surface with new dimensions
- Rebuilds menu screens with updated layout

#### 4. Renderer (`boneglaive/graphical/renderer.py`)
- `change_resolution()`: Dynamically changes resolution during gameplay
- Reinitializes UI components with new layout
- Clears render caches to force redraw
- Updates camera and tile size for proper coordinate transformation

## How Resolution Changes Work

1. **User Selection**: Player navigates to Settings → Display Settings and cycles through resolutions
2. **Pending Change**: Selected resolution marked as pending, Apply button appears
3. **Apply**: When Apply is clicked:
   - New resolution saved to config.json
   - Display surface recreated at new resolution
   - All UI components rebuilt with scaled dimensions
   - Fonts rescaled proportionally
4. **Immediate Effect**: Changes apply instantly without restart

## Layout Calculations

The layout system uses proportional ratios:
- Left panel: 18.9% of screen width
- Right panel: 18.9% of screen width
- Game board: Remaining width (62.2%)
- Top bar: 6.25% of screen height
- Bottom bar: 10% of screen height

Tile size is calculated as: `game_board_width / 20` (for 20x10 grid)

## Font Scaling

Fonts scale based on average of width and height ratios:
```python
scale = (width_ratio + height_ratio) / 2
scaled_size = max(8, int(base_size * scale))  # Minimum 8px
```

## Configuration Storage

Resolution settings stored in `config.json`:
```json
{
  "window_width": 1920,
  "window_height": 1080,
  "fullscreen": false
}
```

## Testing

Run unit tests (no display required):
```bash
python test_resolution_unit.py
```

## Common Issues and Solutions

### Issue: UI elements overlap at low resolutions
**Solution**: Minimum resolution enforced at 1280x720. Font minimum size prevents text becoming unreadable.

### Issue: Resolution doesn't fit display
**Solution**: Settings menu filters available resolutions based on `pygame.display.list_modes()`.

### Issue: Fullscreen doesn't work properly
**Solution**: Fullscreen flag passed to `pygame.display.set_mode()`. Toggle applies immediately without resolution change.

### Issue: Cached graphics don't update
**Solution**: `_clear_render_cache()` clears terrain tiles, sparkle cache, and marks grid dirty for full redraw.

## Future Improvements

1. **Aspect Ratio Preservation**: Currently uses uniform scaling (min of x/y scale). Could add letterboxing for non-native aspects.
2. **Window Resize Events**: Could handle dynamic window resizing via pygame.VIDEORESIZE events.
3. **DPI Awareness**: High-DPI display support for crisp rendering on 4K/Retina displays.
4. **Performance**: Optimize scaling for 4K resolution (currently excluded for stability).
5. **Preset Profiles**: Save resolution profiles for different displays (laptop vs external monitor).

## Developer Notes

- Always use `layout.scale_font_size()` for font sizes
- Use `layout` properties for all UI dimensions (never hardcode pixel values)
- Test at minimum (1280x720) and maximum (2560x1440) resolutions
- Camera system handles all coordinate transformations (screen ↔ grid)
- UI components must accept `layout` parameter in constructor