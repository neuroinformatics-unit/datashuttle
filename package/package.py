import shutil
import subprocess
import zipfile
from pathlib import Path

import requests

# Constants
WEZTERM_VERSION = "20240203-110809-5046fc22"
WEZTERM_FOLDERNAME = f"WezTerm-windows-{WEZTERM_VERSION}"
WEZTERM_URL = f"https://github.com/wezterm/wezterm/releases/download/{WEZTERM_VERSION}/{WEZTERM_FOLDERNAME}.zip"

# Paths
project_root = Path(__file__).parent
base_path = Path.cwd()
vendored_dir = base_path / "_vendored"
wezterm_extracted_dir = vendored_dir / f"WezTerm-windows-{WEZTERM_VERSION}"
wezterm_zip_path = vendored_dir / f"{WEZTERM_FOLDERNAME}.zip"

# Step 1: Download and extract WezTerm if missing
if not wezterm_extracted_dir.exists():
    print("⬇ Downloading WezTerm...")
    vendored_dir.mkdir(parents=True, exist_ok=True)
    with requests.get(WEZTERM_URL, stream=True) as response:
        response.raise_for_status()
        with open(wezterm_zip_path, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

    print("📦 Extracting WezTerm...")
    with zipfile.ZipFile(wezterm_zip_path, "r") as zipf:
        zipf.extractall(vendored_dir)
    wezterm_zip_path.unlink()  # Optional: clean up ZIP
    print("✅ WezTerm ready.")
else:
    print("✅ WezTerm already present. Skipping download.")

shutil.copy(
    base_path / "wezterm_config.lua", vendored_dir / WEZTERM_FOLDERNAME
)

# Step 2: Run PyInstaller builds
subprocess.run(f"pyinstaller {project_root / 'datashuttle.spec'}")
subprocess.run(f"pyinstaller {project_root / 'terminal_launcher.spec'}")

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
