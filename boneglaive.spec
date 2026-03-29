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
    # Cairo and its full dependency tree
    cairo_dlls = [
        'libcairo-2.dll',
        'libcairo-gobject-2.dll',
        'libpixman-1-0.dll',
        'libfontconfig-1.dll',
        'libfreetype-6.dll',
        'libpng16-16.dll',
        'zlib1.dll',
        'libexpat-1.dll',
        'libharfbuzz-0.dll',
        'libglib-2.0-0.dll',
        'libgobject-2.0-0.dll',
        'libintl-8.dll',
        'libiconv-2.dll',
        'libpcre2-8-0.dll',
        'libffi-8.dll',
        'libbz2-1.dll',
        'libbrotlidec.dll',
        'libbrotlicommon.dll',
        'libgraphite2.dll',
    ]
    for dll in cairo_dlls:
        dll_path = os.path.join(msys2_bin, dll)
        if os.path.exists(dll_path):
            extra_binaries.append((dll_path, '.'))

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
        'cairocffi',
        'cairocffi._generated.ffi',
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
