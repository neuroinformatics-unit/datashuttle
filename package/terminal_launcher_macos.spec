# -*- mode: python ; coding: utf-8 -*-
import os

TARGET_ARCH = os.environ.get("TARGET_ARCH") or None
MACOS_MIN_VERSION = os.environ.get("MACOS_MIN_VERSION", "10.13.0")
DATASHUTTLE_VERSION = os.environ.get("DATASHUTTLE_VERSION", "0.0.0")

a = Analysis(
    ['terminal_launcher_macos.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='terminal_launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=TARGET_ARCH,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='terminal_launcher',
)

app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    name='Datashuttle.app',
    icon=None,
    bundle_identifier='dev.neuroinformatics.datashuttle',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleDisplayName': 'Datashuttle',
        'CFBundleName': 'Datashuttle',
        'CFBundleIdentifier': 'dev.neuroinformatics.datashuttle',
        'CFBundleVersion': DATASHUTTLE_VERSION,
        'CFBundleShortVersionString': DATASHUTTLE_VERSION,
        'NSPrincipalClass': 'NSApplication',
        'LSMinimumSystemVersion': MACOS_MIN_VERSION,
    }
)
