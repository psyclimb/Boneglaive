#!/usr/bin/env python3
"""
Boneglaive2 Installation Script
Automatically installs pygame and other dependencies
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def is_module_installed(module_name):
    """Check if a module is already installed."""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def install_pygame():
    """Install pygame using pip."""
    print("🎮 Installing pygame...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
        print("✅ pygame installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install pygame")
        print("   Try running: pip install pygame")
        return False

def install_windows_curses():
    """Install windows-curses on Windows."""
    if sys.platform == "win32":
        print("🪟 Installing windows-curses for Windows...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "windows-curses"])
            print("✅ windows-curses installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install windows-curses")
            return False
    return True

def main():
    """Main installation process."""
    print("🎯 Boneglaive2 Installation")
    print("=" * 30)
    
    if not check_python_version():
        sys.exit(1)
    
    success = True
    
    # Check pygame
    if is_module_installed("pygame"):
        print("✅ pygame already installed")
    else:
        success &= install_pygame()
    
    # Check windows-curses
    if sys.platform == "win32":
        if is_module_installed("curses"):
            print("✅ curses support already available")
        else:
            success &= install_windows_curses()
    
    if success:
        print("\n🎉 Installation complete!")
        print("   You can now run:")
        print("   • Text mode: python boneglaive/main.py")
        print("   • Graphical mode: Set display_mode to 'graphical' in config.json")
    else:
        print("\n❌ Installation failed")
        print("   Please install dependencies manually:")
        print("   pip install pygame")
        if sys.platform == "win32":
            print("   pip install windows-curses")

if __name__ == "__main__":
    main()