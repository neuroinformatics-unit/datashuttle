# pyinstaller/run_in_terminal.py

import os
import platform
import subprocess
import sys
from pathlib import Path

import packaging_utils


def main():
    print("RUNNING")

    WEZTERM_VERSION = packaging_utils.get_wezterm_version()

    print("WEZTERM_VERSION", WEZTERM_VERSION)

    if platform.system() == "Windows":
        if getattr(sys, "frozen", False):
            # Running as a bundled executable
            base_path = Path(sys.executable).parent
        else:
            # Running as a script
            base_path = Path(__file__).resolve().parent

        wezterm_path = (
            Path(__file__).parent.parent
            / f"_vendored\WezTerm-windows-{WEZTERM_VERSION}"
        )
        wezterm_exe_path = wezterm_path / "wezterm-gui.exe"
        wezterm_config_path = wezterm_path / "wezterm_config.lua"
        exe = base_path / "datashuttle" / "datashuttle.exe"

    elif platform.system() == "Darwin":
        # This is a hot mess, almost direct copy from above.
        if getattr(sys, "frozen", False):
            # Running as a bundled executable
            base_path = Path(sys.executable).parent.parent
        else:
            # Running as a script
            base_path = Path(__file__).resolve().parent.parent

        wezterm_path = base_path / f"_vendored/WezTerm-macos-{WEZTERM_VERSION}"
        wezterm_exe_path = (
            wezterm_path / "Wezterm.app/Contents/MacOS/wezterm-gui"
        )
        wezterm_config_path = wezterm_path / "wezterm_config.lua"

        exe = base_path / "datashuttle"

    # https://github.com/wezterm/wezterm/releases/download/20240203-110809-5046fc22/WezTerm-macos-20240203-110809-5046fc22.zip

    print("BaSE PATH", base_path)
    print("CWD", os.getcwd())
    print("HELLO WORLD")
    print("EXE", exe)
    print("TERMINAL EXE", wezterm_exe_path)
    print("CONFIG", wezterm_config_path.as_posix())

    system = platform.system()

    env = os.environ.copy()
    env["WEZTERM_CONFIG_FILE"] = str(wezterm_config_path.as_posix())

    if system == "Windows":
        cmd = f'"{wezterm_exe_path}" start -- "{exe}"'

        subprocess.Popen(cmd, shell=True, env=env)

    elif system == "Darwin":
        cmd = f"""{wezterm_exe_path} start -- sh -c 'echo "Starting datashuttle..."; "{exe}"'"""

        subprocess.Popen(cmd, shell=True, env=env)
    else:
        subprocess.run(exe)


if __name__ == "__main__":
    main()
