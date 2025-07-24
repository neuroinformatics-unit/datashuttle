import platform
import shutil
import subprocess
import zipfile
from pathlib import Path
import packaging_utils
import requests

WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-macos-{WEZTERM_VERSION}"
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
subprocess.run(f"pyinstaller {project_root / 'terminal_launcher_macos.spec'}", shell=True)

app_macos_path = project_root / "dist" / "Datashuttle.app" / "Contents" / "Resources"

shutil.copytree(vendored_dir / f"{WEZTERM_FOLDERNAME}", app_macos_path / "_vendored" / f"{WEZTERM_FOLDERNAME}")

shutil.copytree(project_root / "dist" / "datashuttle" / "_internal", app_macos_path.parent / "Resources" / "_internal")

shutil.copy(project_root / "dist" / "datashuttle" / "datashuttle", app_macos_path.parent / "Resources")

shutil.copy(
    project_root / "wezterm_config.lua", app_macos_path.parent / "Resources" / "_vendored" / WEZTERM_FOLDERNAME
)
