import os
import subprocess
from pathlib import Path

dir_path = Path(os.path.dirname(os.path.realpath(__file__))).as_posix()

my_env = os.environ.copy()

# TODO: if on windows, suggest they install windows terminal

my_str = """ """
for key, value in os.environ.items():
    if "CONDA" in key or key == "PATH":
        my_str += f"""
            {key}='{Path(value).as_posix()}',"""
message = (
    """
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     font = wezterm.font({family = "Cascadia Mono", weight="DemiLight" }),
     font_size = 10.0,
     set_environment_variables = { """
    + my_str
    + """
    },
}
"""
)
#     exit_behavior = "Hold",
with open(f"{dir_path}/wezterm/.wezterm.lua", "w") as text_file:
    text_file.write(message)

print("start conda run -n datashuttle {dir_path.as_posix()}/app.py")
subprocess.Popen(
    f"{dir_path}/wezterm/wezterm.exe --config-file {dir_path}/wezterm/.wezterm.lua start conda activate datashuttle && python {dir_path}/app.py",
    env=my_env,
)  # noqa
