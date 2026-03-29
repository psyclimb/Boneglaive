"""
PyInstaller runtime hook: ensure bundled Cairo DLLs are discoverable on Windows.

This runs before ANY other imports, so it must set up the DLL search path
before cairocffi attempts its ctypes dlopen calls.
"""
import sys
import os

if sys.platform == 'win32':
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

    # 1. Prepend to PATH (ctypes fallback search)
    os.environ['PATH'] = bundle_dir + os.pathsep + os.environ.get('PATH', '')

    # 2. os.add_dll_directory — required on Python 3.8+ for reliable DLL loading
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(bundle_dir)
        except OSError:
            pass

    # 3. Pre-load libcairo-2.dll explicitly via ctypes so cairocffi finds it
    #    by handle rather than name search. This is the most reliable method.
    import ctypes
    import ctypes.util

    _cairo_dll = os.path.join(bundle_dir, 'libcairo-2.dll')
    if os.path.exists(_cairo_dll):
        try:
            ctypes.CDLL(_cairo_dll)
        except OSError:
            pass
