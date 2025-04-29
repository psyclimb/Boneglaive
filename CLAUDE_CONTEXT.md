# Current Work Context

## Project Status
We are refactoring the Boneglaive codebase following the plan outlined in REFACTORING_ROADMAP.md.

## Current Task
Centralizing animation parameters in the animations.py module:

1. **Implementation Status**:
   - Created `ANIMATION_DEFINITIONS` in animations.py to store all animation parameters
   - Implemented centralized animation for Pry skill with `play_pry_animation()`
   - Updated Pry skill code to use the centralized animation system
   - Added ability to override animations via asset manager while using defaults as fallback

2. **Next Steps**:
   - Extend this approach to other skills (Vault, Judgement, Autoclave)
   - Add more skill definitions to ANIMATION_DEFINITIONS 
   - Consider adding global animation speed multiplier from config.json
   - Improve skill animation code to directly use the centralized definitions

3. **Files Modified**:
   - `/boneglaive/utils/animations.py` - Added ANIMATION_DEFINITIONS and play_pry_animation
   - `/boneglaive/game/skills/glaiveman.py` - Updated Pry skill to use centralized animation

4. **Current Progress**:
   - Completed centralized animation system architecture
   - One skill (Pry) refactored to use the new system
   - Confirmed all animations still work correctly

## Reference Information
- Animation speed parameter is already defined in config.json (animation_speed: 1.0)
- Original animation information for skills is stored in the asset manager
- Each skill animation involves multiple stages (preparation, execution, impact, etc.)
- The unified animations.py module now contains both utility functions and definitions

## Important Observations
- This approach successfully separates animation details from game logic
- The animation definitions can be extended to support global speed multipliers
- Skills can be refactored one at a time without affecting others