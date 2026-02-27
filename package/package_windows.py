import os
import shutil
import subprocess
from pathlib import Path

import packaging_utils
from make_inno_setup_script import make_inno_setup_script

WEZTERM_VERSION = packaging_utils.get_wezterm_version()
WEZTERM_FOLDERNAME = f"WezTerm-windows-{WEZTERM_VERSION}"
WEZTERM_URL = f"https://github.com/wezterm/wezterm/releases/download/{WEZTERM_VERSION}/{WEZTERM_FOLDERNAME}.zip"

project_root = Path(__file__).parent
vendored_dir = project_root / "_vendored"

# Before we start, remove leftover folders from a previous builds
if (build_path := project_root / "build").exists():
    shutil.rmtree(build_path)

if (dist_path := project_root / "dist").exists():
    shutil.rmtree(dist_path)

# First, download Wezterm to be vendored
if not (vendored_dir / WEZTERM_FOLDERNAME).exists():
    packaging_utils.download_wezterm(vendored_dir, WEZTERM_FOLDERNAME)

# Run pyinstaller that will create the datashuttle executable. This is
# the executable that we will later call through the vendored Wezterm terminal.
subprocess.run(
    [
        "pyinstaller",
        str(project_root / "datashuttle.spec"),
        "--distpath",
        str(project_root / "dist"),
        "--workpath",
        str(project_root / "build"),
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
        str(project_root / "terminal_launcher_windows.spec"),
        "--distpath",
        str(project_root / "dist"),
        "--workpath",
        str(project_root / "build"),
        "--noconfirm",
        "--clean",
    ],
    check=True,
)

# Now we create the distribution folder, that contains the datashuttle executable,
# terminal launcher executable, vendored Wezterm and all auxillary files
dist_dir = project_root / "dist"
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

# Copy the datashuttle license
shutil.copy(project_root / "license.txt", dist_dir)

# Copy the datashuttle icon
shutil.copy(project_root / "NeuroBlueprint_icon.ico", dist_dir)

# Copy the Wezterm configuration file
shutil.copy(
    project_root / "wezterm_config.lua",
    project_root / "dist" / "_vendored" / WEZTERM_FOLDERNAME,
)
breakpoint()
# Finally, we will parcel the distribution folder into an installer.
# The output of this step is shipped, and when run will install the
# distribution in the correct place on the system, create shortcuts etc.
# Inno setup runs through a script, we generate it dynamically, removing
# and old versions before we start.
inno_path = project_root / "inno_complie_script.iss"

if os.path.isfile(inno_path):
    os.remove(inno_path)
f = open(inno_path, "a")

text = make_inno_setup_script("0.0.0", str(project_root))

f.write(text.strip())
f.close()

# Run inno set up on the generated script.
subprocess.call(rf"C:\Program Files (x86)\Inno Setup 6\iscc {inno_path}")
