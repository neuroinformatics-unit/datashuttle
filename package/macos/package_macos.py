import os
import platform
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

# Paths.
#   this_dir     -> package/macos/   (location of this script + macOS-specific files)
#   package_root -> package/         (shared files: datashuttle.spec, packaging_utils, etc.)
#   repo_root    -> repo root        (top-level LICENSE etc.)
# `package_root` is added to sys.path so `import packaging_utils` keeps
# working after the split. `sign_macos` lives next to this file so it is
# imported via its absolute location on sys.path (this_dir).
this_dir = Path(__file__).resolve().parent
package_root = this_dir.parent
repo_root = package_root.parent
sys.path.insert(0, str(package_root))
sys.path.insert(0, str(this_dir))

import packaging_utils  # noqa: E402
import sign_macos  # noqa: E402

try:
    DATASHUTTLE_VERSION = version("datashuttle")
except PackageNotFoundError as exc:
    raise RuntimeError(
        "datashuttle is not installed in the current Python environment; "
        "run `pip install .` (or `pip install -e .`) before packaging."
    ) from exc

# Architecture is set by CI via TARGET_ARCH (x86_64 or arm64); fall back to host.
TARGET_ARCH = os.environ.get("TARGET_ARCH") or platform.machine()
# Make sure the spec files see the version so it ends up in Info.plist.
os.environ.setdefault("DATASHUTTLE_VERSION", DATASHUTTLE_VERSION)

WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-macos-{WEZTERM_VERSION}"

# The vendored WezTerm cache is shared across Windows + macOS builds, so we
# anchor it at the package root rather than under windows/ or macos/.
vendored_dir = package_root / "_vendored"

# Clean previous outputs before starting.
for stale in ("build", "dist", "Output"):
    stale_path = this_dir / stale
    if stale_path.exists():
        shutil.rmtree(stale_path)

if not (vendored_dir / WEZTERM_FOLDERNAME).exists():
    packaging_utils.download_wezterm(vendored_dir, WEZTERM_FOLDERNAME)

# Build the datashuttle executable and the terminal-launcher .app bundle.
# `datashuttle.spec` lives in `package/` (shared with Windows), but build/dist
# outputs are pinned under `package/macos/` so the two platforms never
# clobber each other when built on the same machine.
subprocess.run(
    [
        "pyinstaller",
        str(package_root / "datashuttle.spec"),
        "--distpath",
        str(this_dir / "dist"),
        "--workpath",
        str(this_dir / "build"),
        "--noconfirm",
        "--clean",
    ],
    check=True,
)
subprocess.run(
    [
        "pyinstaller",
        str(this_dir / "terminal_launcher_macos.spec"),
        "--distpath",
        str(this_dir / "dist"),
        "--workpath",
        str(this_dir / "build"),
        "--noconfirm",
        "--clean",
    ],
    check=True,
)

app_resources = (
    this_dir / "dist" / "Datashuttle.app" / "Contents" / "Resources"
)

# Vendor WezTerm inside the .app bundle.
shutil.copytree(
    vendored_dir / WEZTERM_FOLDERNAME,
    app_resources / "_vendored" / WEZTERM_FOLDERNAME,
)

# Copy the datashuttle PyInstaller dist into the .app bundle's Resources.
shutil.copytree(
    this_dir / "dist" / "datashuttle" / "_internal",
    app_resources / "_internal",
)
shutil.copy(
    this_dir / "dist" / "datashuttle" / "datashuttle",
    app_resources,
)

# Vendor the Wezterm config.
shutil.copy(
    package_root / "wezterm_config.lua",
    app_resources / "_vendored" / WEZTERM_FOLDERNAME,
)

# Code-sign the bundle before building the DMG. No-op unless
# MACOS_SIGNING_IDENTITY is set in the environment.
sign_macos.sign_app_bundle(
    this_dir / "dist" / "Datashuttle.app",
    this_dir / "entitlements.plist",
)

# Stage the EULA file alongside the build outputs. We copy from the canonical
# top-level LICENSE so there is a single source of truth, and pass the staged
# path to create-dmg via `--eula` so Finder prompts the user to accept the
# MIT license before mounting the disk image.
license_path = this_dir / "dist" / "license.txt"
shutil.copy(repo_root / "LICENSE", license_path)

# Build a .dmg for distribution.
output_dir = this_dir / "Output"
output_dir.mkdir(exist_ok=True)
# IMPORTANT: This filename format (datashuttle-{version}-{arch}.dmg) must stay
# in sync with the myst_substitutions in docs/source/conf.py, which builds
# the direct download links on the Install page.
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
        "--eula",
        str(license_path),
        str(dmg_path),
        str(this_dir / "dist" / "Datashuttle.app"),
    ],
    check=True,
)

# Notarise and staple the DMG. No-op unless the APPLE_ID / APPLE_TEAM_ID /
# APPLE_APP_SPECIFIC_PASSWORD environment variables are all set.
sign_macos.notarise_and_staple(dmg_path)

print(f"Built installer: {dmg_path}")
