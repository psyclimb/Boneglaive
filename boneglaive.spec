# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Boneglaive.
Produces a single-folder distribution with all assets bundled.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['run_graphical.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('graphics',  'graphics'),
        ('sounds',    'sounds'),
        ('maps',      'maps'),
        ('config.json', '.'),
        ('LICENSE', '.'),
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
    runtime_hooks=[],
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
    icon='graphics/boneglaive_icon.png',
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
