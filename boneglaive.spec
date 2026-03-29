# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Boneglaive.
Produces a single-folder distribution with all assets bundled.
"""
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# On Windows, bundle Cairo and all its dependency DLLs from MSYS2
extra_binaries = []
if sys.platform == 'win32':
    msys2_bin = r'C:\msys64\mingw64\bin'

    # Full Cairo dependency tree for cairosvg/cairocffi
    # Order matters: core libs first, then dependents
    cairo_dlls = [
        # Core Cairo
        'libcairo-2.dll',
        'libcairo-gobject-2.dll',
        # Cairo dependencies
        'libpixman-1-0.dll',
        'libpng16-16.dll',
        'zlib1.dll',
        # Font rendering
        'libfontconfig-1.dll',
        'libfreetype-6.dll',
        'libharfbuzz-0.dll',
        'libgraphite2.dll',
        # XML parsing (fontconfig needs this)
        'libexpat-1.dll',
        # GLib (gobject backend)
        'libglib-2.0-0.dll',
        'libgobject-2.0-0.dll',
        'libgio-2.0-0.dll',
        'libgmodule-2.0-0.dll',
        # i18n / encoding
        'libintl-8.dll',
        'libiconv-2.dll',
        # PCRE (glib dependency)
        'libpcre2-8-0.dll',
        # FFI (gobject/glib dependency)
        'libffi-8.dll',
        # Compression
        'libbz2-1.dll',
        'liblzma-5.dll',
        # Brotli (freetype dependency)
        'libbrotlidec.dll',
        'libbrotlicommon.dll',
        # Windows runtime (MinGW)
        'libwinpthread-1.dll',
        'libgcc_s_seh-1.dll',
        'libstdc++-6.dll',
    ]

    missing = []
    for dll in cairo_dlls:
        dll_path = os.path.join(msys2_bin, dll)
        if os.path.exists(dll_path):
            extra_binaries.append((dll_path, '.'))
        else:
            missing.append(dll)

    if missing:
        print(f"\nWARNING: The following Cairo DLLs were NOT found in {msys2_bin}:")
        for m in missing:
            print(f"  MISSING: {m}")
        print("The Windows build may fail to render SVGs at runtime.\n")
    else:
        print(f"Cairo: all {len(cairo_dlls)} DLLs found in {msys2_bin}")

a = Analysis(
    ['run_graphical.py'],
    pathex=['.'],
    binaries=extra_binaries,
    datas=[
        ('graphics',  'graphics'),
        ('sounds',    'sounds'),
        ('maps',      'maps'),
        ('config.json', '.'),
        ('LICENSE', '.'),
        ('boneglaive/graphical/assets', 'boneglaive/graphical/assets'),
    ],
    hiddenimports=[
        'cairosvg',
        'cairosvg.surface',
        'cairosvg.url',
        'cairocffi',
        'cairocffi._generated.ffi',
        'cairocffi.constants',
        'cairocffi.context',
        'cairocffi.fonts',
        'cairocffi.matrix',
        'cairocffi.patterns',
        'cairocffi.surfaces',
        'cffi',
        'boneglaive.game.dlc_manager',
        'boneglaive.utils.paths',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_cairo.py'],
    excludes=['curses', '_curses'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='boneglaive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='graphics/boneglaive_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='boneglaive',
)
