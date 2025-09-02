import shutil
import subprocess
from pathlib import Path

import packaging_utils

WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-{WEZTERM_VERSION}-Ubuntu20.04.AppImage"
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

# Paths
dist_dir = project_root / "dist"
launcher_subdir = dist_dir / "terminal_launcher_"

shutil.move(dist_dir / "terminal_launcher", launcher_subdir)

# Copy contents of dist/terminal_launcher/ into dist/
for item in launcher_subdir.iterdir():
    dest = dist_dir / item.name
    if item.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(item, dest)
    else:
        shutil.copy2(item, dest)


# TODO COPY LICENSE

shutil.rmtree(launcher_subdir)

vendored_output_path = dist_dir / "_vendored" / "squashfs-root"

shutil.copytree(
    vendored_dir / "squashfs-root",
    vendored_output_path,
    dirs_exist_ok=True,
    symlinks=True,
    copy_function=shutil.copy2,
)

shutil.copy(vendored_dir / WEZTERM_FOLDERNAME, vendored_output_path.parent)


shutil.copy(
    project_root / "license.txt", dist_dir
)  # TODO: NEED TO DO THIS FOR ALL
shutil.copy(project_root / "NeuroBlueprint_icon.ico", dist_dir)

shutil.copy(
    project_root / "wezterm_config.lua",
    vendored_output_path,
)
