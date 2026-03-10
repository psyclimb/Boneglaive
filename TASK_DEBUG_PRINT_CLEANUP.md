# Task: Remove Debug Print Statements from Boneglaive Codebase

## STEP 0: Verify Task Scope (DO THIS FIRST!)

Before starting any work, you **MUST** verify the details and scope of this task:

### 1. Confirm File List and Print Counts
Run these commands to verify which files actually contain debug prints:

```bash
# Count prints in each file
for file in boneglaive/graphical/animations/*.py boneglaive/graphical/*.py boneglaive/graphical/ui/*.py boneglaive/utils/config.py run_graphical.py; do
    count=$(grep -c "print(" "$file" 2>/dev/null || echo "0")
    if [ "$count" != "0" ]; then
        echo "$file: $count prints"
    fi
done
```

### 2. Sample the Debug Print Patterns
Look at actual examples to understand what you're removing:

```bash
# Show sample debug prints from key files
grep -n "print(" boneglaive/graphical/animations/animation_factory.py | head -10
grep -n "print(" boneglaive/graphical/game_state.py | head -5
grep -n "print(" run_graphical.py
```

### 3. Identify User-Facing Messages to Keep
Check run_graphical.py for messages that should be preserved:

```bash
grep "print(" run_graphical.py | grep -E "(Boneglaive|Game|Starting|Exiting|Menu)"
```

### 4. Verify Current Game State
Ensure the game currently runs without errors:

```bash
python3.11 -c "from boneglaive.utils.config import ConfigManager; print('Config imports OK')"
python3.11 -c "from boneglaive.graphical.animations import animation_factory; print('Animations import OK')"
```

### 5. Create Initial Git Checkpoint
**CRITICAL**: Save the current state before any modifications:

```bash
git status  # Check for any uncommitted changes
git add -A  # Stage everything if clean
git commit -m "Checkpoint before debug print cleanup" || echo "Already at clean state"
```

### Expected Findings
After running the above commands, you should see:
- **Total files with prints**: ~17 files
- **Total print statements**: ~150-200 (actual count may vary)
- **Key patterns**: `[AnimationFactory]`, `[GameState]`, `[DEBUG]`, `Info:`, `Warning:`
- **User messages in run_graphical.py**: Startup banner, exit messages
- **All imports pass**: No syntax errors in current state

### Decision Point
After verification:
- **If counts match expectations (~17 files, ~150-200 prints)**: Proceed with cleanup
- **If significantly different**: Ask user to clarify scope before proceeding
- **If imports fail**: Report issues before attempting cleanup

---

## Objective
Remove all debug `print()` statements from the Boneglaive game codebase while preserving:
- All code functionality
- Proper Python syntax and indentation
- User-facing output messages
- Demo file output

## Background
The game is being prepared for release on itch.io. Currently, when running the graphical version, the terminal fills with debug messages like `[AnimationFactory]`, `[GameState]`, `[DEBUG]`, etc. These need to be removed while keeping clean user-facing messages.

## Critical Requirements

### 1. **Preserve Syntax and Indentation**
- **NEVER** leave empty code blocks (try/except/if/elif/else/for/while)
- If a print statement is the only line in a block, replace it with `pass`
- Maintain exact indentation (spaces/tabs as they appear in original)
- Test each file with `python3.11 -m py_compile <file>` after changes

### 2. **What to Remove**
Debug print statements that match these patterns:
- `print(f"[ClassName] ...")` - Any with square bracket prefixes
- `print(f"DEBUG: ...")` or `print(f"[DEBUG] ...")`
- `print(f"Info: ...")` or `print(f"Warning: ...")`
- `print(f"Loaded ...")` or `print(f"Error loading ...")`
- Any diagnostic/tracing output clearly meant for debugging

### 3. **What to Keep**
User-facing messages:
- **run_graphical.py**: Keep startup banner, "Game ended.", "Exiting Boneglaive. Goodbye!"
- **animations/main.py**: This is a demo file - keep ALL output
- Any messages that provide user feedback (not debug traces)

## Files to Process

Based on previous analysis, these files contain debug prints:

### High Priority (Most Prints)
1. `boneglaive/graphical/animations/animation_factory.py` (~68 prints)
2. `boneglaive/graphical/renderer.py` (~98 prints)
3. `boneglaive/graphical/animations/core.py` (~9 prints)
4. `boneglaive/graphical/game_state.py` (~10 prints)

### Medium Priority
5. `boneglaive/graphical/animations/derelictionist.py` (~7 prints)
6. `boneglaive/graphical/animations/mandible_foreman.py` (~7 prints)
7. `boneglaive/graphical/animations/pelotari.py` (~6 prints)
8. `boneglaive/graphical/animations/glaiveman.py` (~5 prints)
9. `boneglaive/graphical/animations/interferer.py` (~4 prints)
10. `boneglaive/graphical/sound_manager.py` (~9 prints)
11. `boneglaive/graphical/ui_adapter.py` (~7 prints)

### Low Priority
12. `boneglaive/graphical/animations/potpourrist.py` (~1 print)
13. `boneglaive/graphical/ui/loto_system.py` (~5 prints)
14. `boneglaive/graphical/ui/play_menu.py` (~1 print)
15. `boneglaive/graphical/ui/upgrade_window.py` (~1 print)
16. `boneglaive/utils/config.py` (~2 prints)
17. `run_graphical.py` (~13 debug prints, keep 9 user-facing)

### DO NOT MODIFY
- `boneglaive/graphical/animations/main.py` - Demo file, keep all output

## Recommended Approach

### Method: Python Script for Safe Removal

Use a Python script to process each file systematically:

```python
import re
import ast

def is_debug_print(line):
    """Check if line is a debug print statement."""
    stripped = line.strip()
    if not stripped.startswith('print('):
        return False

    # Check for debug patterns
    debug_patterns = [
        r'print\([^)]*\[',           # [ClassName] or [DEBUG]
        r'print\([^)]*DEBUG',         # DEBUG anywhere
        r'print\([^)]*Info:',         # Info: messages
        r'print\([^)]*Warning:',      # Warning: messages
        r'print\([^)]*Loaded',        # Loaded messages
        r'print\([^)]*Error loading', # Error loading messages
    ]

    for pattern in debug_patterns:
        if re.search(pattern, stripped):
            return True
    return False

def process_file(filepath):
    """Remove debug prints while preserving structure."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    output_lines = []
    skip_next_empty = False

    for i, line in enumerate(lines):
        if is_debug_print(line):
            # Check if this print is the only statement in a block
            # by looking at indentation of next non-empty line
            indent = len(line) - len(line.lstrip())

            # Look ahead to see if next line is dedented (end of block)
            needs_pass = False
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                if next_line.strip():  # Found next non-empty line
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= indent:
                        needs_pass = True
                    break

            if needs_pass:
                # Replace with pass at same indentation
                output_lines.append(' ' * indent + 'pass\n')
            # else: just skip the line
            continue

        output_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(output_lines)

    return len(lines) - len(output_lines)

# Process each file
files_to_process = [
    'boneglaive/graphical/animations/animation_factory.py',
    'boneglaive/graphical/renderer.py',
    # ... add all files from list above
]

for filepath in files_to_process:
    removed = process_file(filepath)
    print(f"{filepath}: Removed {removed} debug prints")
```

### Alternative: Manual Sed Approach (Risky)

If using sed, you MUST:
1. Create backups first: `cp file.py file.py.backup`
2. Never use simple line deletion - check for empty blocks
3. Test compilation after EVERY file

## Validation Steps

After processing each file:

1. **Syntax Check**:
   ```bash
   python3.11 -m py_compile boneglaive/graphical/animations/animation_factory.py
   ```

2. **Import Check**:
   ```bash
   python3.11 -c "from boneglaive.graphical.animations import animation_factory; print('OK')"
   ```

3. **Full Import Test** (after all files):
   ```bash
   python3.11 -c "from boneglaive.graphical import renderer; from boneglaive.utils.config import ConfigManager; print('All imports OK')"
   ```

4. **Run Game Test** (final verification):
   ```bash
   python3.11 run_graphical.py
   ```
   - Verify no IndentationError or SyntaxError
   - Verify clean terminal output (no debug spam)
   - Verify user messages still appear

## Common Pitfalls to Avoid

### ❌ DO NOT DO THIS:
```python
# Before
except Exception as e:
    print(f"[DEBUG] Error: {e}")

# After (WRONG - empty except block)
except Exception as e:
```

### ✅ DO THIS INSTEAD:
```python
# After (CORRECT - add pass)
except Exception as e:
    pass
```

### ❌ DO NOT DO THIS:
```python
# Using sed to blindly delete print lines
sed -i '/print(/d' file.py  # BREAKS CODE!
```

### ✅ DO THIS INSTEAD:
```python
# Analyze structure, replace appropriately
# Use Python script or careful manual editing
```

## Expected Results

### Before (Terminal Output):
```
[AnimationFactory] Creating NeutronIlluminantCardinal at (500, 300)
[AnimationFactory] Created animation: <NeutronIlluminantCardinal object>
[GameState] Detected new Selenic Backdraft zone on 9 tiles
[DEBUG] network_mode from config: vs_ai
Initializing Boneglaive Graphical Renderer...
```

### After (Terminal Output):
```
Initializing Boneglaive Graphical Renderer...

============================================================
Boneglaive Graphical Version
============================================================
Game starting...
============================================================
```

## Success Criteria

- [ ] All debug print statements removed (~155 total)
- [ ] No syntax errors in any Python file
- [ ] All imports work correctly
- [ ] Game launches without errors
- [ ] Terminal shows clean output (only user-facing messages)
- [ ] run_graphical.py keeps startup banner and exit message
- [ ] animations/main.py unchanged (demo file)
- [ ] No functionality broken

## File Count Summary

Total files to modify: **17 files**
Total print statements to remove: **~155**
Estimated time: 30-45 minutes (careful, methodical approach)

## Final Notes

- **Take your time** - rushing will break syntax
- **Test frequently** - compile check after each file
- **Use git** - commit after each successful file or group
- **Document** - note any issues encountered
- If stuck on a file, restore from git and try different approach

## Recovery Command

If something breaks:
```bash
git checkout boneglaive/graphical/renderer.py  # Restore single file
git checkout .                                  # Restore all files (nuclear option)
```

Good luck! This is a straightforward but detail-oriented task. The key is being methodical and testing frequently.
