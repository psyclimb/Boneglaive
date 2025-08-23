#!/usr/bin/env python3
"""
Build standalone executable using PyInstaller
This creates a single executable that includes pygame and all dependencies
"""

import subprocess
import sys
import os
import shutil

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller already available")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """Build the executable."""
    print("🔨 Building executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (optional)
        "--name", "Boneglaive2",       # Executable name
        "--add-data", "config.json:.",  # Include config file
        "--hidden-import", "pygame",    # Ensure pygame is included
        "--hidden-import", "curses",    # Ensure curses is included
        "boneglaive/main.py"           # Main script
    ]
    
    # Add Windows-specific options
    if sys.platform == "win32":
        cmd.extend(["--hidden-import", "windows-curses"])
    
    try:
        subprocess.check_call(cmd)
        print("✅ Executable built successfully!")
        
        # Find the executable
        if sys.platform == "win32":
            exe_path = "dist/Boneglaive2.exe"
        else:
            exe_path = "dist/Boneglaive2"
            
        if os.path.exists(exe_path):
            print(f"📁 Executable location: {exe_path}")
            print("   Users can run this file directly without installing Python or pygame!")
        else:
            print("❌ Executable not found in expected location")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")

def main():
    """Main build process."""
    print("🎯 Boneglaive2 Executable Builder")
    print("=" * 35)
    
    install_pyinstaller()
    build_executable()
    
    print("\n📝 Next steps:")
    print("   1. Test the executable in dist/")
    print("   2. Distribute the executable to users")
    print("   3. Users can run it without any installation!")

if __name__ == "__main__":
    main()