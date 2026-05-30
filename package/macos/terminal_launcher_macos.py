"""Launch the terminal from inside the frozen, packaged version of datashuttle.

Also works when invoked directly from this script during local testing.

It must know all path-relative parts to the wezterm executable.
These differ subtly between operating systems; the Windows counterpart
of this script is ``terminal_launcher_windows.py``.

This script is the entry point for starting datashuttle in wezterm, as
packaged by ``terminal_launcher_macos.spec``.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Launch the bundled WezTerm with the datashuttle executable."""
    # Get the path relative to the running executable / script.
    if getattr(sys, "frozen", False):
        # Running as a bundled executable (the final, packaged version)
        base_path = Path(sys.executable).parent.parent / "Resources"
    else:
        # Running as a script (for testing)
        base_path = Path(__file__).resolve().parent.parent

    # Locate the vendored WezTerm folder by globbing rather than by
    # reconstructing its name from a version constant. This keeps the
    # WezTerm version pinned in exactly one place
    # (package/packaging_utils.py), and means this launcher has no
    # runtime dependency on the build-time `packaging_utils` module
    # (which would otherwise drag `requests` etc. into the frozen .app).
    vendored_dir = base_path / "_vendored"
    matches = sorted(vendored_dir.glob("WezTerm-macos-*"))
    if not matches:
        raise FileNotFoundError(
            f"No vendored WezTerm folder found under {vendored_dir}."
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Expected exactly one vendored WezTerm folder under "
            f"{vendored_dir}, found {len(matches)}: {matches}."
        )
    wezterm_path = matches[0]
    wezterm_exe_path = wezterm_path / "Wezterm.app/Contents/MacOS/wezterm-gui"
    wezterm_config_path = wezterm_path / "wezterm_config.lua"
    datashutle_executable = base_path / "datashuttle"

    # Start the wezterm terminal, and within it start datashuttle
    env = os.environ.copy()
    env["WEZTERM_CONFIG_FILE"] = str(wezterm_config_path.as_posix())

    cmd = f"""{wezterm_exe_path} start -- sh -c 'echo "Starting datashuttle..."; "{datashutle_executable}"'"""

    subprocess.Popen(cmd, shell=True, env=env)


if __name__ == "__main__":
    main()
