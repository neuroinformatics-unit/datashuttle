import os
import subprocess
from pathlib import Path
from sys import platform

# fmt: off

dir_path = Path(os.path.dirname(os.path.realpath(__file__))).as_posix()

my_env = os.environ.copy()

# TODO: deal with font size

if platform == "win32":  # TODO: really, all windows?
    default_prog_line = ""# default_prog = { 'conda activate datashuttle_conda' }," #  && python " + f"{dir_path}" + "/app.py' },"
    font_line = font = (
        """font = wezterm.font({family = "Cascadia Mono", weight="DemiLight" }),"""
    )
    path_to_wezterm = "_vendored/wezterm/windows/wezterm.exe"
elif platform == "darwin":
    default_prog_line = (
        "default_prog = { 'bash', '-l', '-c', 'conda activate " + f"{my_env['CONDA_DEFAULT_ENV']}" + " && python " + f"{dir_path}" + "/tui/app.py' },")
    font_line = ""
    path_to_wezterm = "_vendored/wezterm/macos/WezTerm.app"
else:
    default_prog_line = (
        "default_prog = { 'bash', '-i', '-c', 'source activate && conda activate " + f"{my_env['CONDA_DEFAULT_ENV']}" + " && python " + f"{dir_path}" + "/tui/app.py' },")
    font_line = ""

my_str = """ """
for key, value in os.environ.items():
    if "CONDA" in key or key == "PATH":  # "(" not in key:  #  !! was in!
        my_str += f"""
            {key}='{Path(value).as_posix()}',"""

#      font = wezterm.font({family = "Cascadia Mono", weight="DemiLight" }),

#     exit_behavior = "Hold"
#      default_prog = { 'zsh', '-l', '-c', 'source activate datashuttle && conda activate datashuttle && python /Users/joeziminski/git_repos/datashuttle/datashuttle/tui/app.py' },,
# TODO: probably cannot rely on default prog is bash, but using zsh (even though setup for zsh) requires shell init... need to test more cross-platform.
# Could ask on wezterm forum too
message = (
    """
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     exit_behavior = "Hold",
     font_size = 12.0,
     """ + default_prog_line + """
     set_environment_variables = { """
    + my_str
    + """
    },
}
"""
)

with open(f"{dir_path}/_vendored/wezterm/.wezterm.lua", "w") as text_file:
    text_file.write(message)

my_env["WEZTERM_CONFIG_FILE"] = f"{dir_path}/_vendored/wezterm/.wezterm.lua"
my_env["CONDA_AUTO_ACTIVATE_BASE"] = "true"

print(f"{dir_path}/{path_to_wezterm}")
if platform == "darwin":
    subprocess.Popen(["open", f"{dir_path}/{path_to_wezterm}"], env=my_env)  # TODO: don't need `path_to_wezterm` anymore.
elif platform == "win32":
    subprocess.Popen(f"{dir_path}/{path_to_wezterm}  start conda activate {my_env['CONDA_DEFAULT_ENV']} && python {dir_path}/tui/app.py", env=my_env)
else:
    subprocess.Popen(f"chmod +x {dir_path}/_vendored/wezterm/linux/wezterm.AppImage")
    subprocess.Popen([f"{dir_path}/_vendored/wezterm/linux/wezterm.AppImage"], env=my_env)

# fmt: on
