# main.spec
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform
from glob import glob
from pathlib import Path
import shutil

# Include .tcss files.
# Anchor the glob at the spec file's location (the `package/` dir) so the
# lookup does not depend on the caller's CWD. SPECPATH is provided by
# PyInstaller when evaluating the spec.
_spec_dir = Path(SPECPATH)
_css_src_dir = (_spec_dir / ".." / "datashuttle" / "tui" / "css").resolve()
_tcss_matches = sorted(_css_src_dir.glob("*.tcss"))
if not _tcss_matches:
    raise FileNotFoundError(
        f"No .tcss files found under {_css_src_dir}; cannot build TUI styles."
    )
tcss_files = [
    (str(f), os.path.join("datashuttle", "tui", "css"))
    for f in _tcss_matches
]

# Get current conda environment prefix
env_prefix = sys.prefix

# Detect OS and set rclone path

rclone_src = shutil.which("rclone")

if rclone_src is None:
    raise FileNotFoundError(
        "rclone not found in PATH. Ensure it is installed before running PyInstaller."
    )

binaries = [(rclone_src, ".")]

a = Analysis(
    ['datashuttle_launcher.py'],  # terminal_launcher
    # Anchor pathex on SPECPATH (the spec file's directory) rather than on
    # the caller's CWD, so PyInstaller can always find the `datashuttle/`
    # source package one level up regardless of where the build is invoked
    # from. `os.path.abspath('..')` would resolve against CWD and silently
    # produce a bundle missing the datashuttle modules.
    pathex=[str((Path(SPECPATH) / "..").resolve())],
    binaries=binaries,
    datas=tcss_files,
    hiddenimports=[
        'datashuttle.tui_launcher',
        'datashuttle.tui.app',
        'textual.widgets._tab_pane',
        'textual.widgets._input',
        'textual.widgets._tree_control',
        'rich._unicode_data.unicode17-0-0'
    ],
    # No custom hooks directory; previously set to the relative path
    # 'hooks' which was both CWD-dependent and pointed at a nonexistent
    # folder. Left empty so the build is fully reproducible.
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
    target_arch=os.environ.get("TARGET_ARCH") or None,
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
    name='datashuttle'
)
