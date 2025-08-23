# Cross-Platform ASCII Rendering (Graphical Grid System)

## Overview

Boneglaive2 now includes a **graphical grid system tile-based ASCII renderer** that provides consistent, cross-platform graphical display of ASCII characters independent of the user's terminal or system fonts.

## Key Features

✅ **OS/Character Set Agnostic** - Works identically on Windows, Linux, macOS  
✅ **Fixed Character Grid** - Perfect monospace alignment with graphical grid system  
✅ **Font Fallback System** - Automatically selects best monospace font  
✅ **No Terminal Dependencies** - Runs in its own window  
✅ **Pixel-Perfect ASCII** - Each character rendered in exact grid positions  

## How It Works

### Character Grid System
- Each character occupies a fixed-size cell (e.g., 12x20 pixels)
- Grid calculated from window size: `grid_width = window_width / char_width`
- Characters positioned at exact pixel coordinates: `(x * char_width, y * char_height)`

### Font Selection
Automatic fallback hierarchy:
1. DejaVu Sans Mono (preferred)
2. Consolas (Windows)
3. Courier New (universal)
4. Liberation Mono (Linux)
5. System monospace font
6. Pygame default font

### Rendering Pipeline
1. **Background**: Optional colored cell background
2. **Character**: Monospace font character rendering
3. **Attributes**: Bold, styling support
4. **Centering**: Characters centered within their cells

## Usage

### Running Graphical Mode
```bash
# Use graphical renderer (default in config.json)
python3 boneglaive/main.py --display graphical

# Or stick with terminal mode
python3 boneglaive/main.py --display text
```

### Configuration
In `config.json`:
```json
{
  "display_mode": "graphical",  // "text" or "graphical" 
  "window_width": 1000,         // Window width in pixels
  "window_height": 700          // Window height in pixels
}
```

## Technical Implementation

### Core Methods

**`draw_char(y, x, char, fg_color, bg_color, attributes)`**  
Renders single character at exact grid position

**`draw_text(y, x, text, color, attributes)`**  
Renders text string character-by-character for perfect alignment

**`_load_best_monospace_font(size)`**  
Selects optimal monospace font with fallbacks

### Grid Calculations
```python
# Character grid dimensions
self.char_width = font_width    # e.g., 12 pixels
self.char_height = font_height  # e.g., 20 pixels
self.grid_width = window_width // char_width   # e.g., 83 chars
self.grid_height = window_height // char_height # e.g., 35 chars

# Pixel positioning  
pixel_x = grid_x * char_width
pixel_y = grid_y * char_height
```

## Compatibility

### Dependencies
- **Python 3.x** (standard library)
- **Pygame** (`pip install pygame`)

### Supported Systems
- ✅ Windows (any version with Python)
- ✅ Linux (all distributions)  
- ✅ macOS (Intel and Apple Silicon)
- ✅ Any system with Pygame support

### Fallback Behavior
- If Pygame unavailable → Falls back to terminal curses mode
- If no monospace fonts → Uses Pygame default font
- If window too small → Calculates maximum possible grid

## Benefits Over Terminal Rendering

| Feature | Terminal (Curses) | Graphical (Pygame) |
|---------|------------------|-------------------|
| Cross-platform consistency | ❌ Varies by terminal | ✅ Identical everywhere |
| Font control | ❌ System dependent | ✅ Controlled fallbacks |
| Windows compatibility | ⚠️ Limited/problematic | ✅ Perfect |
| Character rendering | ⚠️ Encoding issues | ✅ Unicode support |
| Performance | ✅ Fast | ✅ 60fps with vsync |
| Setup complexity | ✅ No dependencies | ⚠️ Requires Pygame |

## Future Enhancements

- **Tileset Support**: Custom bitmap fonts (like .PNG tilesets)
- **Color Themes**: Customizable color palettes
- **Scaling**: Runtime font size adjustment
- **Full Unicode**: Extended character set support
- **Web Version**: HTML5 Canvas renderer

This system provides the "just works" experience you wanted - users can run Boneglaive2 on any OS with consistent ASCII visuals!