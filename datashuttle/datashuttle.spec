# -*- mode: python ; coding: utf-8 -*-


# Include .tcss files
tcss_files = [
    (f, os.path.join("datashuttle", "tui", "css"))
    for f in glob("../datashuttle/tui/css/*.tcss")
]


a = Analysis(
    ['tui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=tcss_files,
    hiddenimports=[
        'datashuttle.tui_launcher',
        'datashuttle.tui.app',
        'textual.widgets._tab_pane',
        'textual.widgets._input',
        'textual.widgets._tree_control',
    ],
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
    name='datashuttle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='datashuttle',
)
