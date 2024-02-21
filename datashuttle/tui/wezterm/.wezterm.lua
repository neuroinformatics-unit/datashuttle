
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     exit_behavior = "Hold",
     font_size = 12.0, 
     default_prog = { 'bash', '-i', '-c', 'source activate && conda activate datashuttle10 && python /home/joe/git-repos/datashuttle/datashuttle/tui/app.py' },
     set_environment_variables = {  
            CONDA_EXE='/home/joe/programs/miniconda3/bin/conda',
            CONDA_PREFIX='/home/joe/programs/miniconda3/envs/datashuttle10',
            CONDA_PROMPT_MODIFIER='(datashuttle10) ',
            _CE_CONDA='.',
            CONDA_SHLVL='2',
            CONDA_PYTHON_EXE='/home/joe/programs/miniconda3/bin/python',
            CONDA_DEFAULT_ENV='datashuttle10',
            PATH='/usr/local/go/bin:/home/joe/programs/miniconda3/envs/datashuttle10/bin:/home/joe/programs/miniconda3/condabin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/home/joe/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/home/joe/go/bin',
            CONDA_PREFIX_1='/home/joe/programs/miniconda3',
    },
}
