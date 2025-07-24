local wezterm = require 'wezterm'

local config = {}

wezterm.on("format-tab-title", function(tab, tabs, panes, config, hover, max_width)
  return {
    { Text = " datashuttle " },
  }
end)

config.initial_rows = 32
config.initial_cols = 115
config.font_size = 12.0

return config