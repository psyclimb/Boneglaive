#!/usr/bin/env python3
"""
One-time script to update all time.sleep() calls in skill animations
to use sleep_with_animation_speed() instead.
"""

import os
import re
import sys

def process_file(file_path):
    """Process a single Python file to replace time.sleep calls"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if we need to add the import
    needs_import = False
    
    # Replace time.sleep() with sleep_with_animation_speed()
    pattern = r'time\.sleep\(([^)]+)\)'
    if re.search(pattern, content):
        needs_import = True
        content = re.sub(pattern, r'sleep_with_animation_speed(\1)', content)
    
    # Add import if needed and not already there
    if needs_import and 'from boneglaive.utils.animation_helpers import sleep_with_animation_speed' not in content:
        import_line = 'from boneglaive.utils.animation_helpers import sleep_with_animation_speed\n'
        # Add after other imports
        if 'import time' in content:
            content = content.replace('import time', 'import time\n' + import_line)
        else:
            # Find a good place to add the import
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i+1, import_line)
                    break
            content = '\n'.join(lines)
    
    # Write back the modified content
    with open(file_path, 'w') as f:
        f.write(content)
    
    return needs_import

def main():
    """Main function to process all skill files"""
    skills_dir = 'boneglaive/game/skills'
    renderer_dir = 'boneglaive/renderers'
    files_modified = 0
    
    # Process skill files
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    files_modified += 1
                    print(f"Modified: {file_path}")
    
    # Process renderer files
    for root, _, files in os.walk(renderer_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    files_modified += 1
                    print(f"Modified: {file_path}")
    
    print(f"\nUpdated {files_modified} files to use animation speed from config")

if __name__ == "__main__":
    main()