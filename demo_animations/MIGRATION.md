# Migration Guide: Monolithic → Modular Demo

## Quick Comparison

### Before (Monolithic)
```
demo_modern_renderer_pygame.py  (5085 lines)
└── Everything in one file
```

### After (Modular)
```
demo_animations/
├── __init__.py          (59 lines)   - Exports
├── core.py              (458 lines)  - Shared framework
├── glaiveman.py         (492 lines)  - GLAIVEMAN animations
├── mandible_foreman.py  (1425 lines) - MANDIBLE FOREMAN animations
├── potpourrist.py       (633 lines)  - POTPOURRIST animations
├── main.py              (2240 lines) - Demo coordinator
└── README.md                         - Documentation
```

## Running

**Old way:**
```bash
python3 demo_modern_renderer_pygame.py
```

**New way:**
```bash
python3 -m demo_animations.main
```

## Importing Animations

**Old way:**
```python
# Had to import from giant file
from demo_modern_renderer_pygame import SpinningGlaiveProjectile
```

**New way:**
```python
# Import only what you need
from demo_animations.glaiveman import SpinningGlaiveProjectile
from demo_animations.potpourrist import DemiluneSwing
from demo_animations.core import ParticleEmitter

# Or import everything
from demo_animations import *
```

## Benefits

| Aspect | Monolithic | Modular |
|--------|-----------|---------|
| **File size** | 5085 lines | 458-2240 lines per module |
| **Navigation** | Scroll through entire file | Jump to unit file directly |
| **Testing** | Test entire demo | Test individual units |
| **Collaboration** | Merge conflicts | Work on separate files |
| **Reusability** | Import giant file | Import specific classes |
| **Extensibility** | Add to giant file | Create new module |

## No Breaking Changes

The original `demo_modern_renderer_pygame.py` is **preserved** for backwards compatibility. Existing code that imports from it will continue to work.

## Recommended Workflow

1. **New development**: Use modular structure (`demo_animations/`)
2. **Legacy code**: Can continue using monolithic file
3. **Gradual migration**: Port unit-by-unit as needed

## Module Organization

Each unit module follows this structure:

```python
#!/usr/bin/env python3
"""
UNIT_NAME Animation Classes
Skill animations for the UNIT_NAME unit.
"""
import pygame
import random
import math
from .core import TILE_SIZE, COLOR_DAMAGE, Particle

class SkillAnimation1:
    # Animation logic
    pass

class SkillAnimation2:
    # Animation logic
    pass
```

The main demo imports and orchestrates all animations:

```python
from .core import *
from .glaiveman import *
from .mandible_foreman import *
from .potpourrist import *

class ModernRendererDemo:
    # Demo coordinator
    pass
```
