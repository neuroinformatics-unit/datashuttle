import os
import platform
import shutil
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import packaging_utils

try:
    DATASHUTTLE_VERSION = version("datashuttle")
except PackageNotFoundError:
    DATASHUTTLE_VERSION = "0.0.0"

# Architecture is set by CI via TARGET_ARCH (x86_64 or arm64); fall back to host.
TARGET_ARCH = os.environ.get("TARGET_ARCH") or platform.machine()
# Make sure the spec files see the version so it ends up in Info.plist.
os.environ.setdefault("DATASHUTTLE_VERSION", DATASHUTTLE_VERSION)

WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-macos-{WEZTERM_VERSION}"

project_root = Path(__file__).parent
vendored_dir = project_root / "_vendored"

# Clean previous outputs before starting.
for stale in ("build", "dist", "Output"):
    stale_path = project_root / stale
    if stale_path.exists():
        shutil.rmtree(stale_path)

if not (vendored_dir / WEZTERM_FOLDERNAME).exists():
    packaging_utils.download_wezterm(vendored_dir, WEZTERM_FOLDERNAME)

# Build the datashuttle executable and the terminal-launcher .app bundle.
subprocess.run(
    [
        "pyinstaller",
        str(project_root / "datashuttle.spec"),
        "--noconfirm",
        "--clean",
    ],
    check=True,
)
subprocess.run(
    [
        "pyinstaller",
        str(project_root / "terminal_launcher_macos.spec"),
        "--noconfirm",
        "--clean",
    ],
    check=True,
)

app_resources = (
    project_root / "dist" / "Datashuttle.app" / "Contents" / "Resources"
)

# Vendor WezTerm inside the .app bundle.
shutil.copytree(
    vendored_dir / WEZTERM_FOLDERNAME,
    app_resources / "_vendored" / WEZTERM_FOLDERNAME,
)

# Copy the datashuttle PyInstaller dist into the .app bundle's Resources.
shutil.copytree(
    project_root / "dist" / "datashuttle" / "_internal",
    app_resources / "_internal",
)
shutil.copy(
    project_root / "dist" / "datashuttle" / "datashuttle",
    app_resources,
)

# Vendor the Wezterm config.
shutil.copy(
    project_root / "wezterm_config.lua",
    app_resources / "_vendored" / WEZTERM_FOLDERNAME,
)

# Build a .dmg for distribution.
output_dir = project_root / "Output"
output_dir.mkdir(exist_ok=True)
dmg_name = f"datashuttle-{DATASHUTTLE_VERSION}-{TARGET_ARCH}.dmg"
dmg_path = output_dir / dmg_name
if dmg_path.exists():
    dmg_path.unlink()

subprocess.run(
    [
        "create-dmg",
        "--volname",
        "Datashuttle",
        "--window-size",
        "600",
        "400",
        "--icon-size",
        "100",
        "--icon",
        "Datashuttle.app",
        "150",
        "200",
        "--app-drop-link",
        "450",
        "200",
        str(dmg_path),
        str(project_root / "dist" / "Datashuttle.app"),
    ],
    check=True,
)

print(f"Built installer: {dmg_path}")
