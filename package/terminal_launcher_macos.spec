# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['terminal_launcher.py'],
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
    target_arch=None,
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
    name='datashuttle.app',  # <- the app bundle name
    icon=None,                     # <- optional .icns file here
    bundle_identifier="com.yourdomain.terminal_launcher",  # optional
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleDisplayName': 'Datashuttle',
        'CFBundleName': 'Datashuttle',
        'CFBundleIdentifier': 'com.yourdomain.datashuttle',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSPrincipalClass': 'NSApplication',
        'LSMinimumSystemVersion': '10.13.0',
    }
)

