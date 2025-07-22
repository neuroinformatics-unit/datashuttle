# pyinstaller/run_in_terminal.py

import platform
import subprocess
from pathlib import Path


def main():
    exe_name = (
        "datashuttle.exe" if platform.system() == "Windows" else "datashuttle"
    )
    import os

    os.getcwd()
    print(os.getcwd())
    terminal_exe = (
        Path(__file__).parent.parent
        / "_vendored\WezTerm-windows-20240203-110809-5046fc22/wezterm-gui.exe"
    )
    config_path = (
        Path(__file__).parent.parent
        / "_vendored\WezTerm-windows-20240203-110809-5046fc22/wezterm_config.lua"
    )

    exe = Path(__file__).parent.parent / exe_name

    if not exe.exists():
        print(f"Error: {exe_name} not found in same folder.")
        return

    system = platform.system()

    env = os.environ.copy()
    env["WEZTERM_CONFIG_FILE"] = str(config_path.as_posix())

    print("HELLO WORLD")
    print("EXE", exe)
    print("TERMINAL EXE", terminal_exe)
    print("CONFIG", config_path.as_posix())

    if system == "Windows":
        subprocess.Popen(f"{terminal_exe} start -- {exe}", shell=True, env=env)

    elif system == "Darwin":
        subprocess.run(
            [
                "osascript",
                "-e",
                f'''tell application "Terminal" to do script "{exe}"''',
            ]
        )

    elif system == "Linux":
        subprocess.run(exe)
    else:
        print("Unsupported platform")


if __name__ == "__main__":
    main()
