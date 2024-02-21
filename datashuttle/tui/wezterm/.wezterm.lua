
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     exit_behavior = "Hold",
     font_size = 12.0,
     default_prog = { 'bash', '-l', '-c', 'conda activate datashuttle_new && python /Users/joeziminski/git_repos/datashuttle/datashuttle/tui/app.py' },
     set_environment_variables = {
            PATH='/opt/homebrew/anaconda3/envs/datashuttle_new/bin:/opt/homebrew/anaconda3/condabin:/Library/Frameworks/Python.framework/Versions/3.10/bin:/Library/Frameworks/Python.framework/Versions/3.9/bin:/Library/Frameworks/Python.framework/Versions/3.8/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/share/dotnet:~/.dotnet/tools',
            CONDA_EXE='/opt/homebrew/anaconda3/bin/conda',
            _CE_CONDA='.',
            CONDA_PYTHON_EXE='/opt/homebrew/anaconda3/bin/python',
            CONDA_SHLVL='2',
            CONDA_PREFIX='/opt/homebrew/anaconda3/envs/datashuttle_new',
            CONDA_DEFAULT_ENV='datashuttle_new',
            CONDA_PROMPT_MODIFIER='(datashuttle_new) ',
            CONDA_PREFIX_1='/opt/homebrew/anaconda3',
    },
}
