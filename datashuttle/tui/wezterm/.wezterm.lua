
-- Pull in the wezterm API
local wezterm = require 'wezterm'

return {
     font_size = 14.0,
     default_prog = { 'bash', '-l', '-c', 'conda activate datashuttle && python /Users/joeziminski/git_repos/datashuttle/datashuttle/tui/app.py' },

     set_environment_variables = {
    },
}
