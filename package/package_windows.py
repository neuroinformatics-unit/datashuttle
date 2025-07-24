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
vendored_dir = base_path / "_vendored"

packaging_utils.download_wezterm(vendored_dir, WEZTERM_FOLDERNAME)

if (build_path := project_root / "build").exists():
    shutil.rmtree(build_path)

if (dist_path := project_root / "dist").exists():
    shutil.rmtree(dist_path)

# Step 2: Run PyInstaller builds
subprocess.run(f"pyinstaller {project_root / 'datashuttle.spec'}", shell=True)
subprocess.run(
    f"pyinstaller {project_root / 'terminal_launcher.spec'}", shell=True
)

shutil.copy(
    base_path / "wezterm_config.lua", vendored_dir / WEZTERM_FOLDERNAME
)

# Step 3: Copy WezTerm into dist/_vendored
dist_dir = base_path / "dist"
terminal_launcher_dist_dir = dist_dir / "terminal_launcher"
vendored_output_path = dist_dir / "_vendored" / wezterm_extracted_dir.name

dist_dir.mkdir(exist_ok=True)

shutil.copytree(
    wezterm_extracted_dir, vendored_output_path, dirs_exist_ok=True
)

# Step 4: Merge terminal_launcher build contents into dist/
for item in terminal_launcher_dist_dir.iterdir():
    target = dist_dir / item.name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)

shutil.rmtree(terminal_launcher_dist_dir)
