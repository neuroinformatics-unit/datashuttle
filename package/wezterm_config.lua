local wezterm = require 'wezterm'

local config = {}

wezterm.on("format-tab-title", function(tab, tabs, panes, config, hover, max_width)
  return {
    { Text = " datashuttle " },
  }
end)

-- ✅ Start maximized (not true fullscreen)
wezterm.on("gui-startup", function(cmd)
  local tab, pane, window = wezterm.mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)

config.initial_rows = 32
config.initial_cols = 132
config.font_size = 11

return config
