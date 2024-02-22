import os
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))
path_to_wezterm = "_vendored/wezterm/windows/wezterm.exe"

subprocess.Popen(f"{dir_path}/{path_to_wezterm}")
