import os
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

# Paths.
#   this_dir     -> package/windows/   (location of this script + windows-specific files)
#   package_root -> package/           (shared files: datashuttle.spec, packaging_utils, etc.)
#   repo_root    -> repo root          (top-level LICENSE etc.)
# `package_root` is added to sys.path so `import packaging_utils` and
# `from make_inno_setup_script import ...` keep working after the split.
this_dir = Path(__file__).resolve().parent
package_root = this_dir.parent
repo_root = package_root.parent
sys.path.insert(0, str(package_root))
sys.path.insert(0, str(this_dir))

import packaging_utils  # noqa: E402
from make_inno_setup_script import make_inno_setup_script  # noqa: E402

try:
    DATASHUTTLE_VERSION = version("datashuttle")
except PackageNotFoundError as exc:
    raise RuntimeError(
        "datashuttle is not installed in the current Python environment; "
        "run `pip install .` (or `pip install -e .`) before packaging."
    ) from exc

WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-windows-{WEZTERM_VERSION}"
WEZTERM_URL = f"https://github.com/wezterm/wezterm/releases/download/{WEZTERM_VERSION}/{WEZTERM_FOLDERNAME}.zip"

# The vendored WezTerm cache is shared across Windows + macOS builds, so we
# anchor it at the package root rather than under windows/ or macos/.
vendored_dir = package_root / "_vendored"

# Before we start, remove leftover folders from a previous builds
if (build_path := this_dir / "build").exists():
    shutil.rmtree(build_path)

if (dist_path := this_dir / "dist").exists():
    shutil.rmtree(dist_path)

# First, download Wezterm to be vendored
if not (vendored_dir / WEZTERM_FOLDERNAME).exists():
    packaging_utils.download_wezterm(vendored_dir, WEZTERM_FOLDERNAME)

# Run pyinstaller that will create the datashuttle executable. This is
# the executable that we will later call through the vendored Wezterm terminal.
# `datashuttle.spec` lives in `package/` (shared with macOS), but build/dist
# outputs are pinned under `package/windows/` so the two platforms never
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

# Now run pyinstaller to create the terminal-launcher executable. It is this
# executable that when run, will open the vendored Wezterm and in it run the
# datashuttle executable created above.

subprocess.run(
    [
        "pyinstaller",
        str(this_dir / "terminal_launcher_windows.spec"),
        "--distpath",
        str(this_dir / "dist"),
        "--workpath",
        str(this_dir / "build"),
        "--noconfirm",
        "--clean",
    ],
    check=True,
)

# Now we create the distribution folder, that contains the datashuttle executable,
# terminal launcher executable, vendored Wezterm and all auxiliary files
dist_dir = this_dir / "dist"
launcher_subdir = dist_dir / "terminal_launcher"

# Copy contents of dist/terminal_launcher/ (the output of pyinstaller packaging of
# terminal launcher) into dist/, one folder level up.
for item in launcher_subdir.iterdir():
    dest = dist_dir / item.name
    if item.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(item, dest)
    else:
        shutil.copy2(item, dest)

# Remove the now-empty terminal_launcher folder
shutil.rmtree(launcher_subdir)

# Copy WezTerm into dist/_vendored
terminal_launcher_dist_dir = dist_dir / "terminal_launcher"
vendored_output_path = dist_dir / "_vendored" / WEZTERM_FOLDERNAME

shutil.copytree(
    vendored_dir / WEZTERM_FOLDERNAME, vendored_output_path, dirs_exist_ok=True
)

# Copy the datashuttle license. We pull from the canonical top-level LICENSE
# file at the repo root so there is a single source of truth; Inno Setup picks
# it up via `LicenseFile=` and displays it as the EULA during install.
shutil.copy(repo_root / "LICENSE", dist_dir / "license.txt")

# Copy the datashuttle icon
shutil.copy(this_dir / "NeuroBlueprint_icon.ico", dist_dir)

# Copy the Wezterm configuration file
shutil.copy(
    package_root / "wezterm_config.lua",
    this_dir / "dist" / "_vendored" / WEZTERM_FOLDERNAME,
)

# Finally, we will parcel the distribution folder into an installer.
# The output of this step is shipped, and when run will install the
# distribution in the correct place on the system, create shortcuts etc.
# Inno setup runs through a script, we generate it dynamically, removing
# any old versions before we start.
inno_path = this_dir / "inno_compile_script.iss"

if os.path.isfile(inno_path):
    os.remove(inno_path)

text = make_inno_setup_script(DATASHUTTLE_VERSION, str(this_dir))

with open(inno_path, "w") as f:
    f.write(text.strip())

# Run Inno Setup on the generated script.
subprocess.run(
    [r"C:\Program Files (x86)\Inno Setup 6\iscc.exe", str(inno_path)],
    check=True,
)
