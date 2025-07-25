import shutil
import subprocess
from pathlib import Path

import packaging_utils

# Constants
WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-windows-{WEZTERM_VERSION}"
WEZTERM_URL = f"https://github.com/wezterm/wezterm/releases/download/{WEZTERM_VERSION}/{WEZTERM_FOLDERNAME}.zip"

# Paths
project_root = Path(__file__).parent
vendored_dir = project_root / "_vendored"

if not (vendored_dir / WEZTERM_FOLDERNAME).exists():
    packaging_utils.download_wezterm(vendored_dir, WEZTERM_FOLDERNAME)

if (build_path := project_root / "build").exists():
    shutil.rmtree(build_path)

if (dist_path := project_root / "dist").exists():
    shutil.rmtree(dist_path)

# Step 2: Run PyInstaller builds
subprocess.run(f"pyinstaller {project_root / 'datashuttle.spec'}", shell=True)
subprocess.run(
    f"pyinstaller {project_root / 'terminal_launcher_windows.spec'}",
    shell=True,
)

# Step 3: Copy WezTerm into dist/_vendored
dist_dir = project_root / "dist"
terminal_launcher_dist_dir = dist_dir / "terminal_launcher"
vendored_output_path = dist_dir / "_vendored" / WEZTERM_FOLDERNAME

shutil.copytree(
    vendored_dir / WEZTERM_FOLDERNAME, vendored_output_path, dirs_exist_ok=True
)
