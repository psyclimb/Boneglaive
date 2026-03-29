"""
PyInstaller runtime hook: ensure bundled Cairo DLLs are discoverable on Windows.
Adds the executable's directory to the DLL search path before cairocffi tries dlopen.
"""
import sys
import os

if sys.platform == 'win32':
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # Add bundle dir to PATH so ctypes can find bundled DLLs
    os.environ['PATH'] = bundle_dir + os.pathsep + os.environ.get('PATH', '')
    # Also use os.add_dll_directory (Python 3.8+) for more reliable DLL loading
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(bundle_dir)
        except OSError:
            pass
