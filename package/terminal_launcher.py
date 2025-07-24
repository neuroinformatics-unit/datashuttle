# pyinstaller/run_in_terminal.py

import os
import platform
import subprocess
from pathlib import Path


def main():
    if platform.system() == "Windows":
        exe_name = "datashuttle.exe"
        wezterm_path = (
            Path(__file__).parent.parent
            / "_vendored\WezTerm-windows-20240203-110809-5046fc22/"
        )
        wezterm_exe_path = wezterm_path / "wezterm-gui.exe"
        wezterm_config_path = wezterm_path / "wezterm_config.lua"
        exe = Path(__file__).parent.parent / exe_name

    elif platform.system() == "Darwin":
        if getattr(sys, "frozen", False):
            # Running as a bundled executable
            base_path = Path(sys.executable).parent.parent / "Resources"
        else:
            # Running as a script
            base_path = Path(__file__).resolve().parent.parent

        wezterm_path = (
            base_path / "_vendored/WezTerm-macos-20240203-110809-5046fc22"
        )  #  / "MacOS" /
        wezterm_exe_path = (
            wezterm_path / "Wezterm.app/Contents/MacOS/wezterm-gui"
        )
        wezterm_config_path = wezterm_path / "wezterm_config.lua"

        exe = base_path / "datashuttle"
    else:
        wezterm_path = None
        wezterm_exe_path = None
        wezterm_config_path = None
        exe_name = "datashuttle"

    # https://github.com/wezterm/wezterm/releases/download/20240203-110809-5046fc22/WezTerm-macos-20240203-110809-5046fc22.zip

    print("CWD", os.getcwd())
    print("HELLO WORLD")
    print("EXE", exe)
    print("TERMINAL EXE", wezterm_exe_path)
    print("CONFIG", wezterm_config_path.as_posix())

    #   if not exe.exists():
    #      print(f"Error: {exe_name} not found in same folder.")
    #     return

    system = platform.system()

    env = os.environ.copy()
    env["WEZTERM_CONFIG_FILE"] = str(wezterm_config_path.as_posix())

    if system == "Windows" or system == "Darwin":
        cmd = f"""{wezterm_exe_path} start -- sh -c 'echo "Starting datashuttle..."; "{exe}"'"""

        subprocess.Popen(cmd, shell=True, env=env)
    else:
        subprocess.run(exe)


if __name__ == "__main__":
    main()
