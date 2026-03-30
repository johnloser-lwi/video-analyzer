# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — GUI build (video-analyzer-gui)."""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all submodules for packages that use dynamic imports
hiddenimports = (
    collect_submodules('ollama')
    + collect_submodules('PIL')
    + collect_submodules('PyQt5')
    + ['sqlite3']
)

# PyQt5 needs its data files (plugins, translations, etc.)
datas = collect_data_files('PyQt5', subdir='Qt5')

a = Analysis(
    ['launcher_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='video-analyzer-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # Windowed app (no terminal)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                  # Add an .icns/.ico path here if you have one
)

# macOS .app bundle (only generated on macOS)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Video Analyzer.app',
        icon=None,              # Add an .icns path here if you have one
        bundle_identifier='com.video-analyzer.gui',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
