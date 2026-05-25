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
# lookup does not depend on the caller's CWD or on PyInstaller's chdir
# behaviour. SPECPATH is provided by PyInstaller; fall back gracefully if
# absent (e.g. when linting the spec outside of PyInstaller).
_spec_dir = Path(globals().get("SPECPATH", os.path.dirname(os.path.abspath(__file__))))
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
    pathex=[os.path.abspath('..')],
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
    hookspath=['hooks'],
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
