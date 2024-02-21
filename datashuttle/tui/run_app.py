import os
import subprocess
from pathlib import Path
from sys import platform

dir_path = Path(os.path.dirname(os.path.realpath(__file__))).as_posix()

my_env = os.environ.copy()

# TODO: deal with font size
if platform == "windows":
    default_prog_line = ""
    font_line = font = (
        """wezterm.font({family = "Cascadia Mono", weight="DemiLight" }),"""
    )
elif platform == "darwin":
    default_prog_line = (
        "default_prog = { 'bash', '-l', '-c', 'conda activate datashuttle && python "
        + f"{dir_path}"
        + "/app.py' },"
    )
    font_line = ""
else:
    default_prog_line = ""
    font_line = ""

my_str = """ """
for key, value in os.environ.items():
    if "(" in key:  # "CONDA" in key or key == "PATH":
        my_str += f"""
            {key}='{Path(value).as_posix()}',"""

#      font = wezterm.font({family = "Cascadia Mono", weight="DemiLight" }),
default_prog = (
    {
        "zsh",
        "-l",
        "-c",
        "conda activate datashuttle && python /Users/joeziminski/git_repos/datashuttle/datashuttle/tui/app.py",
    },
)

#     exit_behavior = "Hold"
#      default_prog = { 'zsh', '-l', '-c', 'source activate datashuttle && conda activate datashuttle && python /Users/joeziminski/git_repos/datashuttle/datashuttle/tui/app.py' },,
# TODO: probably cannot rely on default prog is bash, but using zsh (even though setup for zsh) requires shell init... need to test more cross-platform.
# Could ask on wezterm forum too
message = (
    """
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     font_size = 14.0,
     """
    + default_prog_line
    + """
     """
    + font_line
    + """
     set_environment_variables = { """
    + my_str
    + """
    },
}
"""
)

with open(f"{dir_path}/wezterm/.wezterm.lua", "w") as text_file:
    text_file.write(message)

my_env["WEZTERM_CONFIG_FILE"] = f"{dir_path}/wezterm/.wezterm.lua"
my_env["CONDA_AUTO_ACTIVATE_BASE"] = "true"
subprocess.Popen(["open", f"{dir_path}/wezterm/WezTerm.app"], env=my_env)
