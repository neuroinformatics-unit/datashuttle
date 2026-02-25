"""
This script launches the terminal from inside the frozen, packaged
version of datashuttle (or from this script, if testing).

It must know all paths relative parts to the wezterm executable.
This differs subtly between operating system, the macOS version
of this script is `terminal_launcher_macos.py`.

This script is the entry point for starting datashuttle
in wezterm, packaged by `terminal_launcher_windows.spec`.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

import packaging_utils


def main():

    WEZTERM_VERSION = packaging_utils.get_wezterm_version()

    # Get the path relative to the running executable / script.
    if getattr(sys, "frozen", False):
        # Running as a bundled executable (the final, packaged version)
        base_path = Path(sys.executable).parent
    else:
        # Running as a script (for testing)
        base_path = Path(__file__).resolve().parent

    # Get all relative paths to the Wezterm executable
    wezterm_path = (Path(__file__).parent.parent / "_vendored"/ f"WezTerm-windows-{WEZTERM_VERSION}")
    wezterm_exe_path = wezterm_path / "wezterm-gui.exe"
    wezterm_config_path = wezterm_path / "wezterm_config.lua"
    datashutle_executable = base_path / "datashuttle" / "datashuttle.exe"

    # Print all vars for debugging:
    print("Local Variables: \n")
    for var in locals():
        print(f"{eval(var)}: {var}\n")

    # Start the Wezterm terminal, and within it start datashuttle
    env = os.environ.copy()
    env["WEZTERM_CONFIG_FILE"] = str(wezterm_config_path.as_posix())

    cmd = f'"{wezterm_exe_path}" start -- "{datashutle_executable}"'

    subprocess.Popen(cmd, shell=True, env=env)

if __name__ == "__main__":
    main()
