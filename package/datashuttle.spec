# main.spec
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform
from glob import glob

# Include .tcss files
tcss_files = [
    (f, os.path.join("datashuttle", "tui", "css"))
    for f in glob("../datashuttle/tui/css/*.tcss")
]

# Get current conda environment prefix
env_prefix = sys.prefix

# Detect OS and set rclone path
if platform.system() == "Windows":
    rclone_src = os.path.join(env_prefix, "bin", "rclone.exe")
else:
    rclone_src = os.path.join(env_prefix, "bin", "rclone")

# Verify rclone exists
if not os.path.isfile(rclone_src):
    raise FileNotFoundError(f"rclone binary not found at: {rclone_src}")

# Add rclone as a binary to be bundled
binaries = [(rclone_src, '.')]

a = Analysis(
    ['datashuttle_launcher.py'],
    pathex=[os.path.abspath('..')],
    binaries=binaries,
    datas=tcss_files,
    hiddenimports=[
        'datashuttle.tui_launcher',
        'datashuttle.tui.app',
        'textual.widgets._tab_pane',
        'textual.widgets._input',
        'textual.widgets._tree_control',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    name='datashuttle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    onefile=True,  # <-- enables one-file mode
)
