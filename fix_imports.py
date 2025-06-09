#!/usr/bin/env python3
"""
Fix imports added by the update_animations.py script.
"""

import os
import re

def fix_file(file_path):
    """Fix imports in a single Python file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the import indentation
    pattern = r'([ \t]*)import time\n(from boneglaive\.utils\.animation_helpers import sleep_with_animation_speed)'
    if re.search(pattern, content):
        content = re.sub(pattern, r'\1import time\n\1from boneglaive.utils.animation_helpers import sleep_with_animation_speed', content)
        
        # Write back the fixed content
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to process all skill files"""
    skills_dir = 'boneglaive/game/skills'
    files_fixed = 0
    
    # Process skill files
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_file(file_path):
                    files_fixed += 1
                    print(f"Fixed imports in: {file_path}")
    
    print(f"\nFixed import indentation in {files_fixed} files")

if __name__ == "__main__":
    main()