
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     font = wezterm.font({family = "Cascadia Mono", weight="Light" }),
     font_size = 10.0,
     set_environment_variables = {
            CONDA_DEFAULT_ENV='datashuttle',
            CONDA_EXE='C:/ProgramData/Miniconda3/Scripts/conda.exe',
            CONDA_PREFIX='C:/ProgramData/Miniconda3/envs/datashuttle',
            CONDA_PREFIX_1='C:/ProgramData/Miniconda3',
            CONDA_PROMPT_MODIFIER='(datashuttle) ',
            CONDA_PYTHON_EXE='C:/ProgramData/Miniconda3/python.exe',
            CONDA_SHLVL='2',
            PATH='C:/ProgramData/Miniconda3/envs/datashuttle;C:/ProgramData/Miniconda3/envs/datashuttle/Library/mingw-w64/bin;C:/ProgramData/Miniconda3/envs/datashuttle/Library/usr/bin;C:/ProgramData/Miniconda3/envs/datashuttle/Library/bin;C:/ProgramData/Miniconda3/envs/datashuttle/Scripts;C:/ProgramData/Miniconda3/envs/datashuttle/bin;C:/ProgramData/Miniconda3/condabin;C:/Program Files/Microsoft/jdk-11.0.12.7-hotspot/bin;C:/Windows/system32;C:/Windows;C:/Windows/System32/Wbem;C:/Windows/System32/WindowsPowerShell/v1.0;C:/Windows/System32/OpenSSH;C:/Program Files/Git/cmd;C:/Program Files/MATLAB/R2021b/bin;c:/users/user/pycharmprojects/ee64_v1.0.0-beta/venv/lib/site-packages/pyinstaller;C:/Users/User/AppData/Local/Programs/Python/Python37/Scripts;c:/users/user/pycharmprojects/ee64_v1.0.0-beta/venv/lib/site-packages/pyinstaller/bootloader/Windows-64bit;C:/Program Files/PuTTY;C:/TDM-GCC-64/bin;C:/Program Files/SafeNet/Authentication/SAC/x64;C:/Program Files/SafeNet/Authentication/SAC/x32;C:/Program Files/dotnet;C:/Program Files/Docker/Docker/resources/bin;C:/ProgramData/chocolatey/bin;C:/Program Files/MiKTeX/miktex/bin/x64;C:/Strawberry/c/bin;C:/Strawberry/perl/site/bin;C:/Strawberry/perl/bin;C:/Program Files/Pandoc;C:/Users/User/AppData/Local/Microsoft/WindowsApps;C:/Users/User/.dotnet/tools;C:/Users/User/AppData/Local/JetBrains/Toolbox/scripts;C:/Users/User/Downloads/ffmpeg/bin;C:/data/spike_interface/CatGTWin37App/CatGT-win;.;C:/Users/User/AppData/Local/Programs/Microsoft VS Code/bin',
            _CONDA_EXE='C:/ProgramData/Miniconda3/Scripts/conda.exe',
            _CONDA_ROOT='C:/ProgramData/Miniconda3',
            __CONDA_OPENSLL_CERT_FILE_SET='1',
    },
}
